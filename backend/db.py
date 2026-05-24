import os
from pathlib import Path

from pymongo import MongoClient


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if key.startswith("export "):
            key = key.removeprefix("export ").strip()

        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()


def _get_mongo_settings():
    mongo_uri = os.getenv("MONGO_URI")
    database_name = os.getenv("MONGO_DB")
    collection_name = os.getenv("MONGO_COLLECTION")

    if not mongo_uri or not database_name or not collection_name:
        raise RuntimeError(
            "Не заданы MONGO_URI, MONGO_DB или MONGO_COLLECTION в .env"
        )

    return mongo_uri, database_name, collection_name


_client = None
_database_name = None
_collection_name = None


def connect(mongo_uri: str = None, database: str = None, collection: str = None):
    """Создаёт (и кэширует) MongoClient для повторного использования.

    Если параметры не переданы, используются из окружения / DEFAULT_*.
    """
    global _client, _database_name, _collection_name

    mongo_uri_env, database_env, collection_env = _get_mongo_settings()

    mongo_uri = mongo_uri or mongo_uri_env
    _database_name = database or database_env
    _collection_name = collection or collection_env

    if _client is None:
        _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

    return _client


def get_mongo_collection():
    """Возвращает кэшированную коллекцию. Если клиент не создан — автоматически подключается."""
    global _client, _database_name, _collection_name
    if _client is None:
        raise RuntimeError("MongoClient не инициализирован. Вызовите bd.connect() при старте приложения")

    return _client[_database_name][_collection_name]
