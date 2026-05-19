# api.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from datetime import date

from repository import StatsRepository
from service import StatsService
from models import TrackClickRequest, StatsSummaryResponse

router = APIRouter(prefix="/stats", tags=["statistics"])

def get_service() -> StatsService:
    return StatsService(StatsRepository())

@router.post("/track", status_code=204)
async def track_click(
    request_data: TrackClickRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    service: StatsService = Depends(get_service)
):
    """
    POST /stats/track
    Отслеживает клик по новости. Возвращает 204 No Content.
    """
    client_ip = http_request.client.host if http_request.client else None
    service.track_click(request_data, background_tasks, client_ip)
    return None

@router.get("/{newsId}", response_model=StatsSummaryResponse)
def get_stats(
    newsId: str,
    date_from: date,
    date_to: date,
    service: StatsService = Depends(get_service)
):
    """Получение статистики по новости за период."""
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be <= date_to")
    return service.get_stats(newsId, date_from, date_to)

@router.get("/health")
def health():
    return {"status": "stats service alive"}