from fastapi.testclient import TestClient


def test_valid_query_extracts_known_preferences(client: TestClient) -> None:
    response = client.post("/api/search/interpret", json={"query": "a relaxing farming game"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["query"] == "a relaxing farming game"
    assert "relaxing" in body["preferences"]["tags"]
    assert "farming" in body["preferences"]["tags"]


def test_empty_query_is_rejected(client: TestClient) -> None:
    response = client.post("/api/search/interpret", json={"query": ""})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_too_short_query_is_rejected(client: TestClient) -> None:
    response = client.post("/api/search/interpret", json={"query": "ab"})
    assert response.status_code == 422


def test_long_query_is_rejected(client: TestClient) -> None:
    response = client.post("/api/search/interpret", json={"query": "a" * 501})
    assert response.status_code == 422


def test_missing_query_field_is_rejected(client: TestClient) -> None:
    response = client.post("/api/search/interpret", json={})
    assert response.status_code == 422


def test_invalid_json_body_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/search/interpret",
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code in (400, 422)


def test_conflicting_query_returns_all_matched_signals(client: TestClient) -> None:
    response = client.post("/api/search/interpret", json={"query": "relaxing but competitive multiplayer"})
    assert response.status_code == 200
    tags = response.json()["preferences"]["tags"]
    assert "relaxing" in tags
    assert "competitive" in tags


def test_query_with_no_known_vocabulary_still_returns_free_text(client: TestClient) -> None:
    response = client.post("/api/search/interpret", json={"query": "xyzzy plugh nonsense query"})
    assert response.status_code == 200
    body = response.json()
    assert body["preferences"]["genres"] == []
    assert body["preferences"]["free_text"] == "xyzzy plugh nonsense query"
