# Backend Developer Assignment – Songs API (Python + Flask + MongoDB)

This repository contains a small REST API that exposes song data loaded from a JSON file
into MongoDB and provides endpoints for listing, searching, and rating songs.

> Note: This project is implemented as part of a backend developer assignment.

---

## Tech Stack

- Python 3.9+
- Flask
- MongoDB
- PyMongo
- Docker (for running MongoDB locally)
- pytest (for automated tests)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/berkterek/yousician_backend_assignment_repo.git
cd yousician_backend_assignment_repo
```

### 2. Create virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

All Python dependencies are listed in `requirements.txt`.

---

## Running MongoDB

By default the application connects to:

- `MONGODB_URI` (optional, default: `mongodb://127.0.0.1:27017`)
- `MONGODB_DB_NAME` (optional, default: `songs_db`)

For local development, MongoDB is expected to run in Docker:

```bash
docker run --detach --name songs_db --publish 127.0.0.1:27017:27017 mongo:7.0
```

If the container already exists and you just want to start it again:

```bash
docker start songs_db
```

---

## Seeding the Database (songs.json → MongoDB)

The project includes a `songs.json` file at the repository root.
This file contains the song data in JSON Lines format (one JSON object per line).

To seed MongoDB with this data:

```bash
source .venv/bin/activate
python scripts/seed_songs.py
```

The script will:

1. Connect to `songs_db` and the `songs` collection.
2. Clear any existing documents.
3. Read `songs.json` and insert all songs.

Example output:

```text
Deleted 0 existing documents
Inserted 11 songs
```

---

## Running the API

```bash
source .venv/bin/activate
python src/app.py
```

The API will be available at:

- `http://127.0.0.1:5000`

---

## Environment Variables

The following environment variables can be used to override defaults:

- `MONGODB_URI` – Mongo connection string (default: `mongodb://127.0.0.1:27017`)
- `MONGODB_DB_NAME` – Database name (default: `songs_db`)

Example:

```bash
export MONGODB_URI="mongodb://127.0.0.1:27017"
export MONGODB_DB_NAME="songs_db"
python src/app.py
```

---

## API Endpoints

All endpoints return JSON.

### 1. Healthcheck

**GET** `/health`

Example response:

```json
{
  "status": "ok"
}
```

---

### 2. List Songs (with pagination)

**GET** `/songs`

Query parameters:

- `page` (optional, default: `1`)
- `page_size` (optional, default: `10`, max: `100`)

Example:

```bash
curl "http://127.0.0.1:5000/songs?page=1&page_size=5"
```

Example response:

```json
{
  "items": [
    {
      "id": "693e9ae56a120fa8e9eee768",
      "artist": "The Yousicians",
      "title": "Lycanthropic Metamorphosis",
      "difficulty": 14.6,
      "level": 13,
      "released": "2016-10-26"
    }
  ],
  "page": 1,
  "page_size": 5,
  "total": 11
}
```

---

### 3. Average Difficulty

**GET** `/songs/difficulty`

Query parameters:

- `level` (optional, integer)  
  - If provided, the average is calculated only for that level.
  - If omitted, the average is calculated over all songs.

Examples:

```bash
# all songs
curl "http://127.0.0.1:5000/songs/difficulty"

# only level 9 songs
curl "http://127.0.0.1:5000/songs/difficulty?level=9"
```

Example response (all songs):

```json
{
  "average_difficulty": 10.323636363636364,
  "count": 11,
  "level": null
}
```

---

### 4. Search Songs

**GET** `/songs/search`

Query parameters:

- `message` (required, string) – searched against `artist` and `title`
  using a case-insensitive match.
- `page` (optional, default: `1`)
- `page_size` (optional, default: `10`, max: `100`)

Example:

```bash
curl "http://127.0.0.1:5000/songs/search?message=night"
```

Example response:

```json
{
  "items": [
    {
      "id": "693e9ae56a120fa8e9eee76c",
      "artist": "The Yousicians",
      "title": "Wishing In The Night",
      "difficulty": 10.98,
      "level": 9,
      "released": "2016-01-01"
    }
  ],
  "message": "night",
  "page": 1,
  "page_size": 10,
  "total": 1
}
```

---

### 5. Add Rating

**POST** `/ratings`

Request body (JSON):

```json
{
  "song_id": "<Mongo ObjectId string>",
  "rating": 1
}
```

Rules:

- `rating` must be an integer between **1 and 5** (inclusive).
- `song_id` must be a valid Mongo ObjectId string.
- The song must exist in the `songs` collection; otherwise the API returns `404`.

Example:

```bash
curl -X POST "http://127.0.0.1:5000/ratings"   -H "Content-Type: application/json"   -d '{"song_id":"693e9ae56a120fa8e9eee768","rating":5}'
```

Successful response (`201 Created`):

```json
{
  "id": "<rating document id>",
  "song_id": "693e9ae56a120fa8e9eee768",
  "rating": 5
}
```

Error examples:

- Missing `song_id` or `rating` → `400`
- Rating outside 1–5 → `400`
- Invalid `song_id` format → `400`
- Song not found → `404`

---

### 6. Rating Statistics

**GET** `/ratings/<song_id>/stats`

Returns aggregated rating statistics for the given song:

- `average_rating`
- `min_rating`
- `max_rating`
- `count`

Example:

```bash
curl "http://127.0.0.1:5000/ratings/693e9ae56a120fa8e9eee768/stats"
```

If ratings exist:

```json
{
  "song_id": "693e9ae56a120fa8e9eee768",
  "average_rating": 5.0,
  "min_rating": 5,
  "max_rating": 5,
  "count": 1
}
```

If there are no ratings yet for that song:

```json
{
  "song_id": "693e9ae56a120fa8e9eee768",
  "average_rating": null,
  "min_rating": null,
  "max_rating": null,
  "count": 0
}
```

---

## Tests

The project includes automated tests using `pytest`.

To run all tests:

```bash
source .venv/bin/activate
pytest -q
```

The test suite covers:

- `/health` endpoint
- `/songs` pagination logic
- Average difficulty calculations (all songs and per level)
- Search behavior (case-insensitive)
- Adding ratings and computing rating statistics
- Validation of invalid rating values

---

## Implementation Notes

- A separate test database (`songs_db_test`) is used in the test suite:
  - Seeded from `songs.json` for every test run.
  - Dropped after tests complete.
- Indexes:
  - `songs.level` – to optimize difficulty aggregation filtered by level.
  - Text index on `(artist, title)` – to optimize search queries.
  - `ratings.song_id` – to speed up rating aggregations per song.
- The API is designed to be simple but scalable:
  - Pagination on list endpoints.
  - MongoDB aggregation pipelines for efficient statistics.
