# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pymongo import ASCENDING, DESCENDING

from database import connect_to_mongo, close_mongo_connection, get_collection
from api import router
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongo()
    # Дополнительно: индексы уже создаются в репозитории, но можно и здесь
    yield
    close_mongo_connection()

app = FastAPI(title="Statistics Subsystem", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)