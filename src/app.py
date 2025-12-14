import os

from flask import Flask, jsonify, request, current_app
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId

def create_app():
    app = Flask(__name__)

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "songs_db")

    client = MongoClient(mongo_uri)
    db = client[db_name]

    app.config["DB_CLIENT"] = client
    app.config["DB"] = db

    songs_col = db["songs"]
    songs_col.create_index("level")
    songs_col.create_index([("artist", "text"), ("title", "text")])

    ratings_col = db["ratings"]
    ratings_col.create_index("song_id")

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

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/songs")
    def list_songs():
        """
        GET /songs?page=1&page_size=10
        Return simple pagination by song list.
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

    @app.get("/songs/difficulty")
    def average_difficulty():
        """
        GET /songs/difficulty
        GET /songs/difficulty?level=9

        It returns the average difficulty for all songs or for a specific level.
        """
        db = current_app.config["DB"]
        songs_col = db["songs"]

        level = request.args.get("level", type=int)

        pipeline = []
        if level is not None:
            pipeline.append({"$match": {"level": level}})

        pipeline.append({
            "$group": {
                "_id": None,
                "average_difficulty": {"$avg": "$difficulty"},
                "count": {"$sum": 1},
            }
        })

        result = list(songs_col.aggregate(pipeline))

        if not result:
            return jsonify({
                "average_difficulty": None,
                "count": 0,
                "level": level,
            })

        stats = result[0]

        return jsonify({
            "average_difficulty": stats["average_difficulty"],
            "count": stats["count"],
            "level": level,
        })

    @app.get("/songs/search")
    def search_songs():
        """
        GET /songs/search?message=foo

        Case-insensitive search on artist + title.
        """
        db = current_app.config["DB"]
        songs_col = db["songs"]

        message = request.args.get("message", type=str)
        page = request.args.get("page", default=1, type=int)
        page_size = request.args.get("page_size", default=10, type=int)

        if not message:
            return jsonify({"error": "message query parameter is required"}), 400

        if page < 1 or page_size < 1 or page_size > 100:
            return jsonify({
                "error": "page and page_size must be positive integers, page_size <= 100"
            }), 400

        skip = (page - 1) * page_size

        regex = {"$regex": message, "$options": "i"}
        query = {"$or": [{"artist": regex}, {"title": regex}]}

        cursor = songs_col.find(query).skip(skip).limit(page_size)
        items = [serialize_song(doc) for doc in cursor]

        total = songs_col.count_documents(query)

        return jsonify({
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "message": message,
        })

    @app.post("/ratings")
    def add_rating():
        """
        POST /ratings
        Body: { "song_id": "<id>", "rating": 1..5 }

        It adds a rating to the song.
        """
        db = current_app.config["DB"]
        songs_col = db["songs"]
        ratings_col = db["ratings"]

        data = request.get_json() or {}

        song_id = data.get("song_id")
        rating = data.get("rating")

        if song_id is None or rating is None:
            return jsonify({"error": "song_id and rating are required"}), 400

        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return jsonify({"error": "rating must be an integer between 1 and 5"}), 400

        if rating < 1 or rating > 5:
            return jsonify({"error": "rating must be between 1 and 5"}), 400

        try:
            song_object_id = ObjectId(song_id)
        except (InvalidId, TypeError):
            return jsonify({"error": "song_id must be a valid ObjectId"}), 400

        song = songs_col.find_one({"_id": song_object_id})
        if not song:
            return jsonify({"error": "song not found"}), 404

        result = ratings_col.insert_one({
            "song_id": song_object_id,
            "rating": rating,
        })

        return jsonify({
            "id": str(result.inserted_id),
            "song_id": song_id,
            "rating": rating,
        }), 201

    @app.get("/ratings/<song_id>/stats")
    def rating_stats(song_id):
        """
        GET /ratings/<song_id>/stats

        The average, lowest, and highest ratings for the given song will be returned.
        """
        db = current_app.config["DB"]
        ratings_col = db["ratings"]

        try:
            song_object_id = ObjectId(song_id)
        except (InvalidId, TypeError):
            return jsonify({"error": "song_id must be a valid ObjectId"}), 400

        pipeline = [
            {"$match": {"song_id": song_object_id}},
            {
                "$group": {
                    "_id": "$song_id",
                    "average_rating": {"$avg": "$rating"},
                    "min_rating": {"$min": "$rating"},
                    "max_rating": {"$max": "$rating"},
                    "count": {"$sum": 1},
                }
            },
        ]

        result = list(ratings_col.aggregate(pipeline))

        if not result:
            return jsonify({
                "song_id": song_id,
                "average_rating": None,
                "min_rating": None,
                "max_rating": None,
                "count": 0,
            })

        stats = result[0]
        return jsonify({
            "song_id": song_id,
            "average_rating": stats["average_rating"],
            "min_rating": stats["min_rating"],
            "max_rating": stats["max_rating"],
            "count": stats["count"],
        })

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
