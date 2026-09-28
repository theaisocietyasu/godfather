import os
import sys

import pytest

os.environ.setdefault('RUNPOD_API_KEY', 'test-runpod-key')
os.environ.setdefault('DISCORD_BOT_TOKEN', 'test-bot-token')
os.environ.setdefault('DISCORD_GUILD_ID', '1000')
os.environ.setdefault('ADMIN_ROLE_ID', '2000')
os.environ.setdefault('GODFATHER_TOKEN_SECRET', 'x' * 40)
os.environ.setdefault('MONGODB_URI', 'mongodb://localhost:27017/godfather-test')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FakeCollection:
    """In-memory stand-in for the few pymongo calls the SSH service makes"""

    def __init__(self):
        self.docs = []

    def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def update_one(self, query, update, upsert=False):
        if self.find_one(query) is None and upsert:
            self.docs.append({**query, **update.get('$setOnInsert', {})})

    def insert_one(self, doc):
        self.docs.append(doc)


@pytest.fixture
def ssh_keys(monkeypatch):
    from domains.ssh import service
    collection = FakeCollection()
    monkeypatch.setattr(service, 'ssh_keys_collection', collection)
    return collection


@pytest.fixture
def app():
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
