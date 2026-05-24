# config.py
import os

class Settings:
    DEFAULT_PAGE: int = 1
    DEFAULT_LIMIT: int = 20
    MAX_LIMIT: int = 100
    SUMMARY_HEADLINES_LIMIT: int = int(os.getenv("SUMMARY_HEADLINES_LIMIT", "5"))

settings = Settings()