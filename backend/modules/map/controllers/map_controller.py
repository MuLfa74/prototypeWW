from fastapi import APIRouter, Query

from modules.map.usecases.map_usecase import MapUseCase


router = APIRouter()
usecase = MapUseCase()

FIXED_BOUNDS = {
    "north": 61.866972,
    "south": 61.703389,
    # Keep west <= east; otherwise bounds filter becomes unsatisfiable.
    "west": 34.087028,
    "east": 34.654750,
}


@router.get("/api/events/map")
def get_map_events(
    category: str = Query(None),
    location: str = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
):
    filters = {}

    if category:
        filters["category"] = category
    if location:
        filters["location"] = location

    result = usecase.get_map_news(FIXED_BOUNDS, filters, limit=limit)
    return {"data": result}
