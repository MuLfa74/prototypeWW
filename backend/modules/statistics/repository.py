# repository.py
from datetime import date
from typing import List
from pymongo import ASCENDING
from db import get_mongo_collection

class StatsRepository:
    def __init__(self):
        # Используем коллекцию "daily_stats" для статистики
        self.collection = get_mongo_collection("daily_stats")
        # Индекс будет создаваться в lifespan main.py, чтобы не создавать каждый раз

    def upsert_daily_stats(self, newsId: str, date_obj: date, source: str) -> None:
        """Атомарно увеличить счётчик кликов."""
        self.collection.update_one(
            {"newsId": newsId, "date": date_obj, "source": source},
            {"$inc": {"clicks": 1}},
            upsert=True
        )

    def get_stats_by_news_id(self, newsId: str, date_from: date, date_to: date) -> List[dict]:
        """Выборка агрегированных данных за период."""
        cursor = self.collection.find(
            {
                "newsId": newsId,
                "date": {"$gte": date_from, "$lte": date_to}
            },
            {"_id": 0, "date": 1, "source": 1, "clicks": 1}
        ).sort("date", ASCENDING)
        return list(cursor)