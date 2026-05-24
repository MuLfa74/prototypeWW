import re
from db import get_mongo_collection


class MapRepository:
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

    def get_news(self, bounds: dict, filters: dict, date_range: dict, limit: int = 1000):
        clauses = []

        if date_range:
            clauses.append(self._date_clause(date_range))

        if bounds:
            clauses.append(self._bounds_clause(bounds))

        if filters.get("category"):
            clauses.append({"category": filters["category"]})

        if filters.get("source"):
            clauses.append({"source": filters["source"]})

        if filters.get("location"):
            clauses.append(self._location_clause(filters["location"]))

        query = {"$and": [clause for clause in clauses if clause]}

        cursor = self.collection.find(query).sort("date", -1).limit(limit)
        return self._dedupe_by_header(list(cursor))

    def _date_clause(self, date_range: dict):
        # Use safe conversion so malformed date values do not crash the whole query.
        return {
            "$expr": {
                "$and": [
                    {
                        "$gte": [
                            {
                                "$convert": {
                                    "input": "$date",
                                    "to": "date",
                                    "onError": None,
                                    "onNull": None,
                                }
                            },
                            date_range["from"],
                        ]
                    },
                    {
                        "$lte": [
                            {
                                "$convert": {
                                    "input": "$date",
                                    "to": "date",
                                    "onError": None,
                                    "onNull": None,
                                }
                            },
                            date_range["to"],
                        ]
                    },
                ]
            }
        }

    def _bounds_clause(self, bounds: dict):
        north = float(bounds["north"])
        south = float(bounds["south"])
        east = float(bounds["east"])
        west = float(bounds["west"])

        # Normalize bounds so west <= east even if input is swapped.
        west, east = min(west, east), max(west, east)

        inside_clauses = []

        for latitude_field, longitude_field in (
            ("geodata.lat", "geodata.lon"),
            ("coordinates.lat", "coordinates.lon"),
            ("location.lat", "location.lon"),
            ("position.lat", "position.lon"),
        ):
            inside_clauses.append(
                {
                    latitude_field: {"$gte": south, "$lte": north},
                    longitude_field: {"$gte": west, "$lte": east},
                }
            )

        # Support collector format: geodata.coordinates = [lat, lon]
        inside_clauses.append(
            {
                "geodata.coordinates.0": {"$gte": south, "$lte": north},
                "geodata.coordinates.1": {"$gte": west, "$lte": east},
            }
        )

        # Also support reversed order: geodata.coordinates = [lon, lat]
        inside_clauses.append(
            {
                "geodata.coordinates.1": {"$gte": south, "$lte": north},
                "geodata.coordinates.0": {"$gte": west, "$lte": east},
            }
        )

        missing_coordinates_clause = {
            "geodata": {"$exists": False},
            "coordinates": {"$exists": False},
            "location": {"$exists": False},
            "position": {"$exists": False},
        }

        return {"$or": inside_clauses + [missing_coordinates_clause]}

    def _location_clause(self, location: str):
        pattern = re.escape(location)

        return {
            "$or": [
                {"location": {"$regex": pattern, "$options": "i"}},
                {"city": {"$regex": pattern, "$options": "i"}},
                {"place": {"$regex": pattern, "$options": "i"}},
                {"region": {"$regex": pattern, "$options": "i"}},
            ]
        }
