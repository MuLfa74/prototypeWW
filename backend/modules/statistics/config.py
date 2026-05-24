# config.py
import os

class Settings:
    HOST: str = os.getenv("STATS_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("STATS_PORT", "8001"))

settings = Settings()