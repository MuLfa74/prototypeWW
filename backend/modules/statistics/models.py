# models.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

class SourceEnum(str, Enum):
    FEED = "feed"
    SEARCH = "search"
    DIGEST = "digest"
    EMAIL = "email"

class TrackClickRequest(BaseModel):
    """Входные данные для трекинга клика (от новостного сервиса)."""
    newsId: str
    userId: Optional[str] = None
    source: SourceEnum

    @field_validator('newsId')
    def validate_news_id(cls, v):
        if not v or len(v) < 5:
            raise ValueError('newsId must be non-empty')
        return v

class ClickEventInternal(BaseModel):
    """Внутреннее событие после обогащения."""
    newsId: str
    userId: Optional[str]
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip: Optional[str] = None

class DailyStatsResponse(BaseModel):
    date: date
    source: str
    clicks: int

class StatsSummaryResponse(BaseModel):
    newsId: str
    period_from: date
    period_to: date
    stats: List[DailyStatsResponse]