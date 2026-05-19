# models.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from bson import ObjectId

class GeoData(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]

class EventInDB(BaseModel):
    """Модель события, как хранится в MongoDB."""
    id: str = Field(alias="_id")
    header: str
    content: str
    annotation: Optional[str] = None
    category: str
    date: datetime
    geodata: Optional[GeoData] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @field_validator("id", mode="before")
    def convert_objectid(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

class NewsOut(BaseModel):
    """Для списка новостей (без полного content и geodata)."""
    id: str
    header: str
    annotation: Optional[str]
    date: datetime
    category: str

class NewsDetail(NewsOut):
    """Полная новость с content и geodata."""
    content: str
    geodata: Optional[GeoData] = None

class DailySummary(BaseModel):
    date: datetime
    headlines: List[str]
    summary_text: str
    total_news_count: int

class NewsFilters(BaseModel):
    date: Optional[datetime] = None   # ожидается дата (день)
    category: Optional[str] = None

class PaginationParams(BaseModel):
    page: int = Field(ge=1, default=1)
    limit: int = Field(ge=1, le=100, default=20)