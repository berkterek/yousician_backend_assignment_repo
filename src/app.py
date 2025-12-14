from flask import Flask, jsonify, request, current_app
from pymongo import MongoClient


def create_app():
    app = Flask(__name__)

    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client["songs_db"]
    app.config["DB"] = db

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    def serialize_song(doc):
        """MongoDB docs JSON-friendly convert."""
        return {
            "id": str(doc["_id"]),
            "artist": doc.get("artist"),
            "title": doc.get("title"),
            "difficulty": doc.get("difficulty"),
            "level": doc.get("level"),
            "released": doc.get("released"),
        }

    @app.get("/songs")
    def list_songs():
        """
        GET /songs?page=1&page_size=10

        Simple pagination by song list.
        """
        db = current_app.config["DB"]
        songs_col = db["songs"]

        page = request.args.get("page", default=1, type=int)
        page_size = request.args.get("page_size", default=10, type=int)

        if page < 1 or page_size < 1 or page_size > 100:
            return jsonify({
                "error": "page and page_size must be positive integers, page_size <= 100"
            }), 400

        skip = (page - 1) * page_size

        cursor = songs_col.find().skip(skip).limit(page_size)
        items = [serialize_song(doc) for doc in cursor]

        total = songs_col.count_documents({})

        return jsonify({
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        })

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
