# repositories/search_repository.py
from elasticsearch import Elasticsearch
# репозиторий для взаимодействия с Elasticsearch и выполнения запросов на поиск и фильтрацию событий
class SearchRepository:
    def __init__(self):
        self.es = Elasticsearch("http://localhost:9200")
        self.index = "news"

    def search(self, query: str, filters: dict):
        must = []
        filter_clauses = []

        if query:
            must.append({
                "multi_match": {
                    "query": query,
                    "fields": ["header", "content", "annotation"]
                }
            })

        if "category" in filters:
            filter_clauses.append({
                "term": {"category": filters["category"]}
            })

        if "date_from" in filters or "date_to" in filters:
            range_query = {}
            if "date_from" in filters:
                range_query["gte"] = filters["date_from"]
            if "date_to" in filters:
                range_query["lte"] = filters["date_to"]

            filter_clauses.append({
                "range": {"date": range_query}
            })

        body = {
            "query": {
                "bool": {
                    "must": must,
                    "filter": filter_clauses
                }
            }
        }

        response = self.es.search(index=self.index, body=body)

        return [hit["_source"] for hit in response["hits"]["hits"]]

    def filter(self, filters: dict):
        return self.search(query=None, filters=filters)