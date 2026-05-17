# контроллер для обработки запросов на поиск и фильтрацию событий
from fastapi import APIRouter, Query
from usecases.search_usecase import SearchUseCase

router = APIRouter()
usecase = SearchUseCase()

@router.get("/api/events/search")
def search_events(
    q: str = Query(None),
    category: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
):
    filters = {}

    if category:
        filters["category"] = category
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    result = usecase.search_news(q, filters)
    return {"data": result}


@router.get("/api/events")
def filter_events(
    category: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
):
    filters = {}

    if category:
        filters["category"] = category
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    result = usecase.filter_news(filters)
    return {"data": result}