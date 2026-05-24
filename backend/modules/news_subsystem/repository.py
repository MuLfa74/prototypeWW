# repository.py
from datetime import datetime, time
from typing import List, Optional
from bson import ObjectId
from db import get_mongo_collection
from models import NewsFilters


class NewsRepository:
    def __init__(self):
        # Получаем коллекцию через единый db.py
        self.collection = get_mongo_collection()

    def _dedupe_by_header(self, documents: List[dict]) -> List[dict]:
        seen = set()
        unique_docs = []

        for document in documents:
            header = str(document.get("header") or document.get("title") or "").strip().lower()
            if not header:
                header = str(document.get("_id"))

            if header in seen:
                continue

            seen.add(header)
            unique_docs.append(document)

        return unique_docs

    def find_all(
        self,
        offset: int,
        limit: int,
        filters: Optional[NewsFilters] = None
    ) -> List[dict]:
        """Поиск новостей с пагинацией и фильтрацией."""
        query = {}

        if filters:
            if filters.date:
                # Фильтр по конкретной дате (диапазон с 00:00 до 23:59 UTC)
                start = datetime.combine(filters.date.date(), time.min)
                end = datetime.combine(filters.date.date(), time.max)
                query["date"] = {"$gte": start, "$lte": end}
            if filters.category:
                query["category"] = filters.category

        # Сортировка по дате (новые сначала)
        cursor = self.collection.find(query).sort("date", -1).skip(offset).limit(limit)
        return self._dedupe_by_header(list(cursor))

    def find_by_id(self, event_id: str) -> Optional[dict]:
        """Получение новости по _id."""
        try:
            obj_id = ObjectId(event_id)
        except:
            return None
        return self.collection.find_one({"_id": obj_id})

    def find_all_by_date_range(self, start_date: datetime, end_date: datetime) -> List[dict]:
        """Все новости за временной промежуток (без лимита)."""
        query = {"date": {"$gte": start_date, "$lte": end_date}}
        cursor = self.collection.find(query).sort("date", -1)
        return self._dedupe_by_header(list(cursor))