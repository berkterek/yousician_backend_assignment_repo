# Songs API — Backend Take-Home (Python + Flask + MongoDB)

A small REST API that loads song data from `songs.json` into MongoDB and exposes endpoints for:
- listing songs (pagination)
- searching songs (case-insensitive)
- computing average difficulty (overall / by level)
- adding ratings (1–5)
- rating statistics per song (avg/min/max/count)

> Implemented as a backend developer take-home assignment.

---

## Tech Stack
- Python 3.9+
- Flask
- MongoDB
- PyMongo
- Docker (to run MongoDB locally)
- pytest (tests)

---

## Quickstart (Local)

### 1) Clone
```bash
git clone https://github.com/berkterek/backend_python_mongodb_repo.git
cd backend_python_mongodb_repo
```

### 2) Start MongoDB (Docker)
```bash
docker run --detach --name songs_db --publish 127.0.0.1:27017:27017 mongo:7.0
# if you already have it:
# docker start songs_db
```

### 3) Create venv + install deps
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4) Seed database (songs.json → MongoDB)
```bash
python scripts/seed_songs.py
```

### 5) Run the API
```bash
python src/app.py
```

API runs at:
- http://127.0.0.1:5000

---

## Configuration

Environment variables (optional):
- `MONGODB_URI` (default: `mongodb://127.0.0.1:27017`)
- `MONGODB_DB_NAME` (default: `songs_db`)

Example:
```bash
export MONGODB_URI="mongodb://127.0.0.1:27017"
export MONGODB_DB_NAME="songs_db"
python src/app.py
```

---

## Data Import

- `songs.json` is **JSON Lines** (one JSON object per line).
- Seeding script: `scripts/seed_songs.py`
  - clears existing documents
  - inserts all songs into `songs` collection

---

## API Endpoints

All endpoints return JSON.

### Healthcheck
**GET** `/health`

```bash
curl "http://127.0.0.1:5000/health"
```

Response:
```json
{ "status": "ok" }
```

---

### List songs (pagination)
**GET** `/songs`

Query:
- `page` (default: `1`)
- `page_size` (default: `10`, max: `100`)

```bash
curl "http://127.0.0.1:5000/songs?page=1&page_size=5"
```

Response shape:
```json
{
  "items": [],
  "page": 1,
  "page_size": 5,
  "total": 11
}
```

---

### Average difficulty (overall / by level)
**GET** `/songs/difficulty`

Query:
- `level` (optional integer)

```bash
curl "http://127.0.0.1:5000/songs/difficulty"
curl "http://127.0.0.1:5000/songs/difficulty?level=9"
```

Response shape:
```json
{
  "average_difficulty": 10.32,
  "count": 11,
  "level": null
}
```

---

### Search songs
**GET** `/songs/search`

Query:
- `message` (**required** string) — searched against `artist` and `title` (case-insensitive)
- `page` (default: `1`)
- `page_size` (default: `10`, max: `100`)

```bash
curl "http://127.0.0.1:5000/songs/search?message=night"
```

Response shape:
```json
{
  "items": [],
  "message": "night",
  "page": 1,
  "page_size": 10,
  "total": 1
}
```

---

### Add rating
**POST** `/ratings`

Body:
```json
{
  "song_id": "<Mongo ObjectId string>",
  "rating": 5
}
```

Rules:
- `rating` must be an integer **1..5**
- `song_id` must be a valid Mongo ObjectId string
- Song must exist, otherwise `404`

Example:
```bash
curl -X POST "http://127.0.0.1:5000/ratings" \
  -H "Content-Type: application/json" \
  -d '{"song_id":"693e9ae56a120fa8e9eee768","rating":5}'
```

Success (`201 Created`) shape:
```json
{
  "id": "<rating document id>",
  "song_id": "693e9ae56a120fa8e9eee768",
  "rating": 5
}
```

---

### Rating statistics
**GET** `/ratings/<song_id>/stats`

Returns:
- `average_rating`
- `min_rating`
- `max_rating`
- `count`

```bash
curl "http://127.0.0.1:5000/ratings/693e9ae56a120fa8e9eee768/stats"
```

If no ratings exist yet, values are `null` and `count` is `0`.

---

## Tests

Run:
```bash
source .venv/bin/activate
pytest -q
```

Coverage includes:
- `/health`
- `/songs` pagination
- `/songs/difficulty` (overall + by level)
- `/songs/search` (case-insensitive)
- `POST /ratings` validation + creation
- `/ratings/<song_id>/stats` aggregation

Notes:
- Tests use a separate DB: `songs_db_test`
- Seeded from `songs.json` for each run
- Dropped/cleaned after tests

---

## Implementation Notes / Design Choices

- MongoDB aggregation pipelines are used for statistics (difficulty & rating stats).
- Suggested indexes (implementation-dependent):
  - `songs.level` (optimize level-filtered aggregations)
  - text index on `(artist, title)` (optimize search)
  - `ratings.song_id` (optimize per-song rating stats)

---

## Next Improvements (if productized)
- Add `docker-compose.yml` + one-command `make run`
- OpenAPI/Swagger docs
- Structured error responses + request validation (e.g., pydantic)
- CI (GitHub Actions) to run tests automatically
- Production WSGI server + config (gunicorn, etc.)

---
