"""Database connection and collections"""
from pymongo import MongoClient
from shared.config import settings

client = MongoClient(settings.MONGODB_URI)
db = client.Godfather  # Matches the existing database name (capital G)

# Collections
pods_collection = db.pods
users_collection = db.users
ssh_keys_collection = db.ssh_keys
