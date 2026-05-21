from datetime import datetime, timedelta, timezone

from repositories.map_repo import MapRepository


class MapUseCase:
    def __init__(self):
        self.repo = MapRepository()

    def get_map_news(self, bounds: dict, filters: dict, limit: int = 1000):
        date_range = self._last_week_range()
        news_list = self.repo.get_news(bounds, filters, date_range, limit=limit)
        center = self._bounds_center(bounds)
        return self.normalize_coordinates(news_list, center)

    def normalize_coordinates(self, news_list, center: dict):
        normalized = []

        for news in news_list:
            item = dict(news)
            coordinates = self._extract_coordinates(item)

            if coordinates is None:
                coordinates = center

            item["coordinates"] = coordinates

            if "_id" in item:
                item["_id"] = str(item["_id"])

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

    def _extract_coordinates(self, news: dict):
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