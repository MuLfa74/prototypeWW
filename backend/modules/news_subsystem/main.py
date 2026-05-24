# main.py
import traceback
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pymongo import ASCENDING, DESCENDING
import uvicorn
from db import connect, get_mongo_collection
from api import router
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Подключение к MongoDB через единый db.py")
    connect()  # инициализация клиента (можно без параметров, если .env настроен)
    collection = get_mongo_collection()
    
    print("Создание индексов...")
    collection.create_index([("date", DESCENDING)])
    collection.create_index([("category", ASCENDING)])
    collection.create_index([("date", DESCENDING), ("category", ASCENDING)])
    print("Индексы созданы")
    
    yield
    
    # Закрытие соединения – желательно добавить функцию close() в db.py,
    # но можно и не закрывать явно, если процесс завершается.
    # Если нужно – добавьте close_mongo_connection() в db.py и вызовите здесь.

app = FastAPI(title="News Subsystem (MongoDB)", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)