"""Database connection and collections"""
from pymongo import MongoClient
from config.settings import settings

# Initialize MongoDB client
client = MongoClient(settings.MONGODB_URI)
db = client.godfather

# Collections
pods_collection = db.pods
users_collection = db.users
ssh_keys_collection = db.ssh_keys
