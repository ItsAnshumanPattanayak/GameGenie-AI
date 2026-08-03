from fastapi.testclient import TestClient


def test_basic_recommendation_returns_items(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "a relaxing puzzle game", "limit": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "items" in body
    assert body["result_count"] == len(body["items"])
    assert body["processing_time_ms"] >= 0


def test_limit_is_respected(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "space adventure exploration", "limit": 3},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) <= 3


def test_limit_too_large_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "any game", "limit": 100},
    )
    assert response.status_code == 422


def test_limit_zero_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "any game", "limit": 0},
    )
    assert response.status_code == 422


def test_query_too_short_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "ab", "limit": 5},
    )
    assert response.status_code == 422


def test_ranked_by_final_score_descending(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "puzzle simulation cozy", "limit": 10},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    scores = [item["scores"]["final"] for item in items]
    assert scores == sorted(scores, reverse=True)


def test_rank_starts_at_one(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "cozy puzzle game", "limit": 5},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    if items:
        assert items[0]["rank"] == 1
        for index, item in enumerate(items, start=1):
            assert item["rank"] == index


def test_recommendation_has_explanation(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "cozy puzzle game", "limit": 5},
    )
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert isinstance(item["explanation"], str)
        assert len(item["explanation"]) > 0


def test_recommendation_has_score_breakdown(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "action game with story", "limit": 3},
    )
    assert response.status_code == 200
    expected = {"semantic", "genre", "platform", "tag", "rating", "final"}
    for item in response.json()["items"]:
        assert expected.issubset(item["scores"].keys())


def test_preferences_are_returned(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "puzzle game on PC", "limit": 5},
    )
    assert response.status_code == 200
    prefs = response.json()["preferences"]
    assert "genres" in prefs
    assert "platforms" in prefs
    assert "tags" in prefs
    assert "free_text" in prefs


def test_filter_by_platform(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={
            "query": "any game to play",
            "limit": 10,
            "filters": {"platforms": ["PC"]},
        },
    )
    assert response.status_code == 200
    for item in response.json()["items"]:
        platforms = [p.casefold() for p in item["game"]["platforms"]]
        assert "pc" in platforms


def test_filter_by_min_rating(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={
            "query": "any game to play",
            "limit": 10,
            "filters": {"min_rating": 4.5},
        },
    )
    assert response.status_code == 200
    for item in response.json()["items"]:
        rating = item["game"]["rating"]
        assert rating is None or rating >= 4.5


def test_empty_query_after_strip_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/search/recommend",
        json={"query": "   ", "limit": 5},
    )
    assert response.status_code == 422


def test_missing_query_field_is_rejected(client: TestClient) -> None:
    response = client.post("/api/search/recommend", json={"limit": 5})
    assert response.status_code == 422
