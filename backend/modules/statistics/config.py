# config.py
import os

class Settings:
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "stats_db")
    COLLECTION_NAME: str = "daily_stats"
    HOST: str = "0.0.0.0"
    PORT: int = 8001   # отдельный порт для статистики

settings = Settings()