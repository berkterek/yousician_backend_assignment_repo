import os
import sys
import json
from pathlib import Path

import pytest
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app import create_app

@pytest.fixture()
def app(monkeypatch):
    """
    For each test, a separate Flask app is set up, along with a separate test MongoDB database.
    """
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    test_db_name = "songs_db_test"

    monkeypatch.setenv("MONGODB_URI", mongo_uri)
    monkeypatch.setenv("MONGODB_DB_NAME", test_db_name)

    client = MongoClient(mongo_uri)
    db = client[test_db_name]
    songs_col = db["songs"]
    ratings_col = db["ratings"]

    songs_col.delete_many({})
    ratings_col.delete_many({})

    songs_path = ROOT / "songs.json"
    docs = []
    with songs_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))

    if docs:
        songs_col.insert_many(docs)

    app = create_app()

    yield app

    client.drop_database(test_db_name)
    client.close()

@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()