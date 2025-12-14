import json
from pathlib import Path

from pymongo import MongoClient


def main():
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client["songs_db"]
    songs_col = db["songs"]

    deleted = songs_col.delete_many({})
    print(f"Deleted {deleted.deleted_count} existing documents")

    data_path = Path(__file__).parent.parent / "songs.json"
    if not data_path.exists():
        raise FileNotFoundError(f"songs.json not found at {data_path}")

    docs = []
    with data_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))

    if docs:
        result = songs_col.insert_many(docs)
        print(f"Inserted {len(result.inserted_ids)} songs")
    else:
        print("No songs found in songs.json")


if __name__ == "__main__":
    main()
