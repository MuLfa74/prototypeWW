# api.py
from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime, date
from typing import Optional

from service import NewsService
from repository import NewsRepository
from models import PaginationParams, NewsFilters, NewsOut, NewsDetail, DailySummary

router = APIRouter(prefix="/news", tags=["news"])

def get_news_service() -> NewsService:
    # Репозиторий не требует сессий, можно создать напрямую
    return NewsService(NewsRepository())

@router.get("/", response_model=list[NewsOut])
def get_news(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    date_filter: Optional[date] = Query(None, alias="date"),
    category: Optional[str] = None,
    service: NewsService = Depends(get_news_service)
):
    """Получение списка новостей с пагинацией и фильтрацией."""
    pagination = PaginationParams(page=page, limit=limit)
    filters = NewsFilters(
        date=datetime.combine(date_filter, datetime.min.time()) if date_filter else None,
        category=category
    )
    return service.get_news(pagination, filters)

@router.get("/{news_id}", response_model=NewsDetail)
def get_news_detail(
    news_id: str,
    service: NewsService = Depends(get_news_service)
):
    """Получение полной новости по ID."""
    try:
        return service.get_news_by_id(news_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="News not found")

@router.get("/daily-summary", response_model=DailySummary)
def get_daily_summary(
    date_param: date = Query(default=datetime.today().date(), alias="date"),
    service: NewsService = Depends(get_news_service)
):
    """Ежедневная сводка (дайджест) за указанную дату."""
    target = datetime.combine(date_param, datetime.min.time())
    return service.get_daily_summary(target)