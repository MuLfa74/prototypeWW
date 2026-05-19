# config.py
import os

class Settings:
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "news_db")
    COLLECTION_NAME: str = "events"
    DEFAULT_PAGE: int = 1
    DEFAULT_LIMIT: int = 20
    MAX_LIMIT: int = 100
    SUMMARY_HEADLINES_LIMIT: int = 5

settings = Settings()