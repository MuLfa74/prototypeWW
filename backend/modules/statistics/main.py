# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pymongo import ASCENDING

# Импорт из корневого db.py
from backend.db import connect, close, get_mongo_collection
from api import router
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Подключаемся к MongoDB через единый db.py
    connect()  # использует переменные окружения MONGO_URI, MONGO_DB
    collection = get_mongo_collection("daily_stats")
    
    # Создаём уникальный составной индекс (аналог того, что был в __init__ репозитория)
    collection.create_index(
        [("newsId", ASCENDING), ("date", ASCENDING), ("source", ASCENDING)],
        unique=True
    )
    print("Indexes for statistics collection created")
    
    yield
    
    close()  # закрываем соединение (функцию close() нужно добавить в db.py – см. ниже)

app = FastAPI(title="Statistics Subsystem", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)