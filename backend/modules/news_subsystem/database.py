# database.py
from pymongo import MongoClient
from config import settings

class MongoDB:
    client: MongoClient = None

db = MongoDB()

def connect_to_mongo():
    db.client = MongoClient(settings.MONGODB_URL)
    print("Connected to MongoDB")

def close_mongo_connection():
    if db.client:
        db.client.close()
        print("MongoDB connection closed")

def get_collection():
    return db.client[settings.DATABASE_NAME][settings.COLLECTION_NAME]