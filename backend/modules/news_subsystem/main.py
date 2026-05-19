# main.py
import traceback
import sys

print("Начало загрузки main.py")

try:
    print("Импорт модулей...")
    from fastapi import FastAPI
    from contextlib import asynccontextmanager
    from pymongo import ASCENDING, DESCENDING
    from database import connect_to_mongo, close_mongo_connection, get_collection
    from api import router
    from config import settings
    import uvicorn
    print("Все модули импортированы")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        print("Запуск lifespan: подключение к MongoDB")
        connect_to_mongo()
        collection = get_collection()
        print("Создание индексов...")
        collection.create_index([("date", DESCENDING)])
        collection.create_index([("category", ASCENDING)])
        collection.create_index([("date", DESCENDING), ("category", ASCENDING)])
        print("Индексы созданы")
        yield
        close_mongo_connection()
        print("Соединение закрыто")

    app = FastAPI(title="News Subsystem (MongoDB)", lifespan=lifespan)
    app.include_router(router)
    print("FastAPI приложение создано")

    if __name__ == "__main__":
        print("Запуск uvicorn сервера на http://0.0.0.0:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)
        print("Сервер остановлен")

except Exception as e:
    print("Критическая ошибка при запуске:")
    traceback.print_exc()
    sys.exit(1)
