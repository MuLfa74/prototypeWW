# service.py
from fastapi import BackgroundTasks
from datetime import datetime, date
import logging
from typing import List

from repository import StatsRepository
from models import TrackClickRequest, ClickEventInternal, DailyStatsResponse, StatsSummaryResponse

logger = logging.getLogger(__name__)

class StatsService:
    def __init__(self, repo: StatsRepository):
        self.repo = repo

    def track_click(self, request: TrackClickRequest, background_tasks: BackgroundTasks, client_ip: str = None) -> None:
        """
        Use Case TrackClick.
        Обогащает событие и отправляет в фоновую задачу (аналог очереди).
        """
        event = ClickEventInternal(
            newsId=request.newsId,
            userId=request.userId,
            source=request.source.value,
            timestamp=datetime.utcnow(),
            ip=client_ip
        )
        background_tasks.add_task(self._update_stats, event)

    def _update_stats(self, event: ClickEventInternal) -> None:
        """
        Use Case TrackUpdateDB.
        Извлекает дату и обновляет статистику в БД.
        """
        try:
            date_obj = event.timestamp.date()
            self.repo.upsert_daily_stats(event.newsId, date_obj, event.source)
        except Exception as e:
            logger.error(f"Failed to update stats: {event.dict()} – {e}")
            # Здесь можно добавить повторную отправку через очередь (Kafka, RabbitMQ)

    def get_stats(self, newsId: str, date_from: date, date_to: date) -> StatsSummaryResponse:
        """Use Case GetStatsByNewsId"""
        docs = self.repo.get_stats_by_news_id(newsId, date_from, date_to)
        stats = [
            DailyStatsResponse(date=doc["date"], source=doc["source"], clicks=doc["clicks"])
            for doc in docs
        ]
        return StatsSummaryResponse(
            newsId=newsId,
            period_from=date_from,
            period_to=date_to,
            stats=stats
        )