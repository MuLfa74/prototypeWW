from datetime import date, datetime, timedelta, timezone

try:
    from bson import ObjectId
except Exception:
    ObjectId = None

from modules.map.repositories.map_repo import MapRepository


class MapUseCase:
    def __init__(self):
        self.repo = MapRepository()

    def get_map_news(self, bounds: dict, filters: dict, limit: int = 1000):
        date_range = self._last_week_range()
        news_list = self.repo.get_news(bounds, filters, date_range, limit=limit)

        # Fallback: if no records for the last week, load without date restriction.
        if not news_list:
            news_list = self.repo.get_news(bounds, filters, None, limit=limit)

        center = self._bounds_center(bounds)
        return self.normalize_coordinates(news_list, center)

    def normalize_coordinates(self, news_list, center: dict):
        normalized = []

        for news in news_list:
            item = self._normalize_document(dict(news))
            coordinates = self._extract_coordinates(item, center)

            if coordinates is None:
                coordinates = center

            item["coordinates"] = coordinates

            normalized.append(item)

        return normalized

    def _last_week_range(self):
        date_to = datetime.now(timezone.utc)
        date_from = date_to - timedelta(days=7)
        return {"from": date_from, "to": date_to}

    def _bounds_center(self, bounds: dict):
        north = float(bounds["north"])
        south = float(bounds["south"])
        east = float(bounds["east"])
        west = float(bounds["west"])

        return {
            "lat": (north + south) / 2,
            "lon": (east + west) / 2,
        }

    def _extract_coordinates(self, news: dict, center: dict = None):
        geodata = news.get("geodata")
        if isinstance(geodata, dict):
            coords = geodata.get("coordinates")
            if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                a = coords[0]
                b = coords[1]
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    if center and "lat" in center and "lon" in center:
                        # Choose the ordering that is closer to the map center.
                        direct_score = abs(a - center["lat"]) + abs(b - center["lon"])
                        swapped_score = abs(b - center["lat"]) + abs(a - center["lon"])
                        if swapped_score < direct_score:
                            return {"lat": b, "lon": a}
                    return {"lat": a, "lon": b}

        for field in ("coordinates", "geodata", "location", "position"):
            value = news.get(field)
            if isinstance(value, dict):
                lat = value.get("lat")
                lon = value.get("lon")

                if lat is not None and lon is not None:
                    return {"lat": lat, "lon": lon}

        lat = news.get("lat")
        lon = news.get("lon")

        if lat is not None and lon is not None:
            return {"lat": lat, "lon": lon}

        return None

    def _normalize_document(self, value):
        if ObjectId is not None and isinstance(value, ObjectId):
            return str(value)

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, dict):
            return {k: self._normalize_document(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._normalize_document(v) for v in value]

        if isinstance(value, tuple):
            return [self._normalize_document(v) for v in value]

        return value
