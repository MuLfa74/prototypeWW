from elasticsearch import Elasticsearch
import json
es = Elasticsearch("http://localhost:9200")


def search_news(query=None, category=None, date_from=None, date_to=None):

    must = []
    filter_ = []

    # текстовый поиск (может быть пустым)
    if query:
        must.append({
            "multi_match": {
                "query": query,
                "fields": ["header", "content", "annotation"]
            }
        })

    # фильтр по категории (может быть пустым)
    if category:
        filter_.append({
            "term": {
                "category": category
            }
        })

    # фильтр по дате (может быть пустым)
    if date_from or date_to:
        range_query = {}

        if date_from:
            range_query["gte"] = date_from
        if date_to:
            range_query["lte"] = date_to

        filter_.append({
            "range": {
                "date": range_query
            }
        })

    # если вообще ничего нет
    if not must and not filter_:
        return []

    body = {
        "query": {
            "bool": {
                "must": must if must else {"match_all": {}},
                "filter": filter_
            }
        }
    }

    res = es.search(index="news", body=body)

    return res["hits"]["hits"]
print("1------------------------------------------------------------")
print(json.dumps(search_news(query="", category="", date_from="", date_to=""), indent=2, ensure_ascii=False))
print("2------------------------------------------------------------")
print(json.dumps(search_news(query="", category="culture", date_from="", date_to=""), indent=2, ensure_ascii=False))
print("3------------------------------------------------------------")
print(json.dumps(search_news(query="", category="", date_from="2026-03-03T18:00:00Z", date_to=""), indent=2, ensure_ascii=False))
print("4------------------------------------------------------------")
print(json.dumps(search_news(query="плОхо", category="culture", date_from="2026-03-03T18:00:00Z", date_to=""), indent=2, ensure_ascii=False))