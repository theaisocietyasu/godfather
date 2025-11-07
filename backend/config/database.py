"""Database connection and collections"""
from pymongo import MongoClient
from config.settings import settings

# Initialize MongoDB client
client = MongoClient(settings.MONGODB_URI)
db = client.Godfather  # Match the existing database name (capital G)

# Collections
pods_collection = db.pods
users_collection = db.users
ssh_keys_collection = db.ssh_keys
