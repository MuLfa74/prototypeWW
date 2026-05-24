import re

from bd import get_mongo_collection


class MapRepository:
    def __init__(self):
        self.collection = get_mongo_collection()

    def get_news(self, bounds: dict, filters: dict, date_range: dict, limit: int = 1000):
        clauses = [self._date_clause(date_range)]

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
        return list(cursor)

    def _date_clause(self, date_range: dict):
        return {
            "$expr": {
                "$and": [
                    {
                        "$gte": [
                            {"$toDate": "$date"},
                            date_range["from"],
                        ]
                    },
                    {
                        "$lte": [
                            {"$toDate": "$date"},
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
