import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/forms", StaticFiles(directory="frontend/forms"), name="forms")

FORMS_DIR = "frontend/forms/"

# Роут для Главной страницы (http://localhost:8000/)
@app.get("/map")
async def get_map_page():
    return FileResponse(os.path.join(FORMS_DIR, "mappage.html"))

@app.get("/")
@app.get("/news")
async def get_news_page():
    return FileResponse(os.path.join(FORMS_DIR, "newspage.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)