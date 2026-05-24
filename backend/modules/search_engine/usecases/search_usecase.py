from modules.search_engine.repositories.search_repo import SearchRepository

class SearchUseCase:
    def __init__(self):
        self.repo = SearchRepository()

    def search_news(self, query: str, filters: dict):
        return self.repo.search(query, filters)

    def filter_news(self, filters: dict):
        return self.repo.filter(filters)
