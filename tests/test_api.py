import math


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"status": "ok"}


def test_list_songs_pagination(client):
    resp = client.get("/songs?page=1&page_size=5")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["page"] == 1
    assert data["page_size"] == 5
    assert data["total"] == 11
    assert len(data["items"]) == 5

    resp2 = client.get("/songs?page=3&page_size=5")
    assert resp2.status_code == 200
    data2 = resp2.get_json()

    assert data2["page"] == 3
    assert data2["page_size"] == 5
    assert data2["total"] == 11
    assert len(data2["items"]) == 1


def test_average_difficulty_all(client):
    resp = client.get("/songs/difficulty")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["count"] == 11
    assert data["level"] is None
    assert math.isclose(data["average_difficulty"], 10.3236363, rel_tol=1e-6)


def test_average_difficulty_level_filter(client):
    resp = client.get("/songs/difficulty?level=9")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["count"] == 3
    assert data["level"] == 9
    assert math.isclose(data["average_difficulty"], 9.6933333, rel_tol=1e-6)


def test_search_songs_case_insensitive(client):
    resp = client.get("/songs/search?message=night")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert "night" in item["title"].lower()


def test_add_rating_and_stats(client):
    resp = client.get("/songs?page=1&page_size=1")
    assert resp.status_code == 200
    song_id = resp.get_json()["items"][0]["id"]

    for r in (4, 5):
        resp_post = client.post(
            "/ratings",
            json={"song_id": song_id, "rating": r},
        )
        assert resp_post.status_code == 201

    resp_stats = client.get(f"/ratings/{song_id}/stats")
    assert resp_stats.status_code == 200
    stats = resp_stats.get_json()

    assert stats["song_id"] == song_id
    assert stats["count"] == 2
    assert stats["min_rating"] == 4
    assert stats["max_rating"] == 5
    assert math.isclose(stats["average_rating"], 4.5, rel_tol=1e-6)


def test_add_rating_invalid_value_rejected(client):
    resp = client.post("/ratings", json={"song_id": "123", "rating": 0})
    assert resp.status_code == 400

    resp2 = client.post("/ratings", json={"song_id": "123", "rating": 6})
    assert resp2.status_code == 400
