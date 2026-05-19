# service.py
from datetime import datetime, time
from typing import List

from repository import NewsRepository
from models import NewsOut, NewsDetail, DailySummary, NewsFilters, PaginationParams
from config import settings

class NewsService:
    def __init__(self, repo: NewsRepository):
        self.repo = repo

    def get_news(self, pagination: PaginationParams, filters: NewsFilters) -> List[NewsOut]:
        """GetNews: список новостей с пагинацией."""
        offset = (pagination.page - 1) * pagination.limit
        docs = self.repo.find_all(offset, pagination.limit, filters)
        return [NewsOut(id=str(doc["_id"]),
                        header=doc["header"],
                        annotation=doc.get("annotation"),
                        date=doc["date"],
                        category=doc["category"]) for doc in docs]

    def get_news_by_id(self, news_id: str) -> NewsDetail:
        """Получение полной новости по ID."""
        doc = self.repo.find_by_id(news_id)
        if not doc:
            raise ValueError("News not found")
        return NewsDetail(
            id=str(doc["_id"]),
            header=doc["header"],
            annotation=doc.get("annotation"),
            date=doc["date"],
            category=doc["category"],
            content=doc["content"],
            geodata=doc.get("geodata")
        )

    def get_daily_summary(self, target_date: datetime) -> DailySummary:
        """GetDailySummary: формирование ежедневной сводки."""
        start = datetime.combine(target_date.date(), time.min)
        end = datetime.combine(target_date.date(), time.max)

        docs = self.repo.find_all_by_date_range(start, end)

        # Ранжирование: берём первые N заголовков (можно улучшить)
        headlines = [doc["header"] for doc in docs[:settings.SUMMARY_HEADLINES_LIMIT]]

        if headlines:
            summary_text = "Главные события дня: " + "; ".join(headlines)
        else:
            summary_text = "За указанную дату новостей не найдено."

        return DailySummary(
            date=target_date,
            headlines=headlines,
            summary_text=summary_text,
            total_news_count=len(docs)
        )