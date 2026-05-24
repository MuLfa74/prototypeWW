import re
from datetime import date, datetime
from db import get_mongo_collection


class SearchRepository:
    def __init__(self):
        self.collection = get_mongo_collection()

    def _dedupe_by_header(self, documents):
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

    def _normalize_value(self, value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, dict):
            return {key: self._normalize_value(item) for key, item in value.items()}

        if isinstance(value, list):
            return [self._normalize_value(item) for item in value]

        if isinstance(value, tuple):
            return [self._normalize_value(item) for item in value]

        return value

    def _serialize_document(self, document: dict) -> dict:
        serialized = self._normalize_value(dict(document))
        if "_id" in serialized:
            serialized["_id"] = str(serialized["_id"])
        return serialized

    def _build_query(self, query: str, filters: dict):
        mongo_query = {}

        if query:
            escaped_query = re.escape(query)
            mongo_query["$or"] = [
                {"header": {"$regex": escaped_query, "$options": "i"}},
                {"content": {"$regex": escaped_query, "$options": "i"}},
                {"annotation": {"$regex": escaped_query, "$options": "i"}},
            ]

        category = filters.get("category")
        if category:
            mongo_query["category"] = category

        date_filter = {}
        if filters.get("date_from"):
            date_filter["$gte"] = filters["date_from"]
        if filters.get("date_to"):
            date_filter["$lte"] = filters["date_to"]
        if date_filter:
            mongo_query["date"] = date_filter

        return mongo_query

    def search(self, query: str, filters: dict):
        mongo_query = self._build_query(query, filters)
        cursor = self.collection.find(mongo_query)
        return [self._serialize_document(document) for document in self._dedupe_by_header(list(cursor))]

    def filter(self, filters: dict):
        return self.search(query=None, filters=filters)
