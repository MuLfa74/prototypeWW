import os
import sys
import traceback
import asyncio
import json
import subprocess
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional
from bson import ObjectId
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure backend package imports that use top-level 'modules' work.
# Add backend/ to sys.path so `import modules...` inside backend files resolves.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_PATH = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

# We'll import backend items lazily at startup (after DB connect)
backend_db_connect = None


app = FastAPI()

# Static mounts
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")

FORMS_DIR = "frontend/forms"
COLLECTOR_DIR = os.path.join(BACKEND_PATH, 'modules', 'collector')
COLLECTOR_SCRIPT = os.path.join(COLLECTOR_DIR, 'run_all_parsers.py')
PARSE_STATUS_FILE = os.path.join(COLLECTOR_DIR, 'parse_status.json')


class TrackSource(str, Enum):
    feed = "feed"
    search = "search"
    digest = "digest"
    email = "email"


class TrackClickPayload(BaseModel):
    newsId: str = Field(..., min_length=1)
    source: TrackSource = TrackSource.feed
    userId: Optional[str] = None


def _load_root_env():
    """Load .env file from project root (prototypeWW/.env) into os.environ if present.
    This helps when environment variables are stored in project root instead of backend/.
    """
    try:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(root_dir, '.env')
        if not os.path.exists(env_path):
            return

        with open(env_path, encoding='utf-8') as f:
            for raw_line in f.read().splitlines():
                line = raw_line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if value and len(value) >= 2 and ((value[0] == value[-1]) and value[0] in ('"', "'")):
                    value = value[1:-1]
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # best-effort loader; don't fail startup if parsing fails
        pass


def _get_collection(name: Optional[str] = None):
    from db import get_mongo_collection
    return get_mongo_collection(name) if name else get_mongo_collection()


def _read_parse_status():
    if not os.path.exists(PARSE_STATUS_FILE):
        return {"last_updated": None, "news_count": 0, "sources": []}

    try:
        with open(PARSE_STATUS_FILE, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        return {
            "last_updated": payload.get("last_updated"),
            "news_count": payload.get("news_count", 0),
            "sources": payload.get("sources", []),
        }
    except Exception:
        return {"last_updated": None, "news_count": 0, "sources": []}


async def _run_parser_process():
    if not os.path.exists(COLLECTOR_SCRIPT):
        print(f"Parser script not found: {COLLECTOR_SCRIPT}")
        return

    def _runner():
        return subprocess.run(
            [sys.executable, COLLECTOR_SCRIPT],
            cwd=COLLECTOR_DIR,
            capture_output=True,
            text=True,
        )

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _runner)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"Parser finished with code {result.returncode}")
    except Exception as exc:
        print(f"Parser run failed: {exc}")


@app.post("/stats/track", status_code=204)
async def track_click(payload: TrackClickPayload):
    """Record a click/open event in the daily_stats collection."""
    # Ignore invalid IDs to keep daily_stats clean and stable for ranking.
    if not ObjectId.is_valid(str(payload.newsId)):
        return None

    stats_collection = _get_collection("daily_stats")
    today_key = date.today().isoformat()
    stats_collection.update_one(
        {
            "newsId": payload.newsId,
            "date": today_key,
            "source": payload.source.value,
        },
        {
            "$inc": {"clicks": 1},
            "$setOnInsert": {"createdAt": datetime.utcnow().isoformat()}
        },
        upsert=True,
    )
    return None


@app.get("/api/news/daily-summary")
async def daily_summary(limit: int = Query(5, ge=1, le=20)):
    """Top viewed news for the last 24h/day, joined with news documents."""
    try:
        stats_collection = _get_collection("daily_stats")
        news_collection = _get_collection()

        today = date.today()
        day_before = today - timedelta(days=1)
        today_key = today.isoformat()
        day_before_key = day_before.isoformat()

        # Take a wider candidate set first, then filter out invalid/missing news IDs.
        candidate_limit = max(limit * 50, 100)
        pipeline = [
            {"$match": {"date": {"$gte": day_before_key, "$lte": today_key}}},
            {"$group": {"_id": "$newsId", "clicks": {"$sum": "$clicks"}}},
            {"$sort": {"clicks": -1}},
            {"$limit": candidate_limit},
        ]
        top_stats = list(stats_collection.aggregate(pipeline))

        news_ids = []
        valid_news_order = []
        for item in top_stats:
            news_id = item.get("_id")
            if not news_id:
                continue
            news_id_str = str(news_id)
            if not ObjectId.is_valid(news_id_str):
                continue
            try:
                news_ids.append(ObjectId(news_id_str))
                valid_news_order.append(news_id_str)
            except Exception:
                continue

        docs_by_id = {}
        if news_ids:
            for doc in news_collection.find({"_id": {"$in": news_ids}}):
                docs_by_id[str(doc["_id"])] = doc

        items = []
        total_clicks = 0
        for stat in top_stats:
            news_id = str(stat.get("_id", ""))
            if not ObjectId.is_valid(news_id):
                continue

            clicks = int(stat.get("clicks", 0))

            doc = docs_by_id.get(news_id)
            if not doc:
                continue

            items.append({
                "newsId": news_id,
                "header": doc.get("header") or doc.get("title") or "Без названия",
                "annotation": doc.get("annotation") or "",
                "category": doc.get("category") or "",
                "clicks": clicks,
                "date": doc.get("date").isoformat() if hasattr(doc.get("date"), "isoformat") else str(doc.get("date", "")),
            })
            total_clicks += clicks

            if len(items) >= limit:
                break

        if items:
            summary_text = "Главные новости за день: " + "; ".join(item["header"] for item in items)
        else:
            summary_text = "За последние сутки просмотры не зафиксированы."

        return {
            "period_from": day_before_key,
            "period_to": today_key,
            "total_clicks": total_clicks,
            "summary_text": summary_text,
            "items": items,
        }
    except Exception as exc:
        return {
            "period_from": date.today().isoformat(),
            "period_to": date.today().isoformat(),
            "total_clicks": 0,
            "summary_text": f"Сводка дня временно недоступна: {exc}",
            "items": [],
        }


@app.get("/api/news/last-updated")
async def last_updated():
    return _read_parse_status()


# === HTML routes (serve raw files from frontend/forms) ===
# Root now serves the map page (authorization/admin removed)
@app.get("/", response_class=FileResponse)
async def root_page():
    return FileResponse(os.path.join(FORMS_DIR, "mappage.html"))


@app.get("/map", response_class=FileResponse)
async def map_page():
    return FileResponse(os.path.join(FORMS_DIR, "mappage.html"))


@app.get("/news", response_class=FileResponse)
async def news_page():
    return FileResponse(os.path.join(FORMS_DIR, "newspage.html"))


@app.on_event("startup")
async def startup_event():
    # Initialize backend DB connection if backend.db.connect is available
    # Try loading project-root .env first (if present)
    _load_root_env()

    # import and call backend.db.connect from backend package
    try:
        from db import connect as backend_db_connect_local
        backend_db_connect_local()
        print("Connected to backend DB")
    except Exception as e:
        print("Warning: backend DB connect failed:", e)

    # Now import and register backend routers (map, search, news) lazily
    try:
        from importlib import import_module, util

        try:
            map_mod = import_module('modules.map.controllers.map_controller')
            app.include_router(map_mod.router)
            print('Registered map router')
        except Exception as ex:
            print('Import map_controller failed:', ex)

        try:
            search_mod = import_module('modules.search_engine.controllers.search_controller')
            app.include_router(search_mod.router)
            print('Registered search router')
        except Exception as ex:
            print('Import search_controller failed:', ex)

        # news_subsystem uses local top-level imports; load it from its folder
        ns_path = os.path.join(BACKEND_PATH, 'modules', 'news_subsystem')
        if os.path.isdir(ns_path):
            if ns_path not in sys.path:
                sys.path.insert(0, ns_path)
            # load api.py as module
            api_file = os.path.join(ns_path, 'api.py')
            if os.path.exists(api_file):
                spec = util.spec_from_file_location('news_subsystem_api', api_file)
                ns_mod = util.module_from_spec(spec)
                spec.loader.exec_module(ns_mod)
                if hasattr(ns_mod, 'router'):
                    app.include_router(ns_mod.router)
                    print('Registered news_subsystem router')
    except Exception as e:
        print('Error while registering backend routers:', e)

    if not getattr(app.state, 'parser_task_started', False):
        app.state.parser_task_started = True

        async def _hourly_parser_loop():
            await _run_parser_process()
            while True:
                await asyncio.sleep(3600)
                await _run_parser_process()

        app.state.parser_task = asyncio.create_task(_hourly_parser_loop())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)