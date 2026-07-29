from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_and_docs(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "GameGenie AI Backend" and body["version"] == "1.0.0"
    assert body["game_count"] >= 20
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_unknown_route_and_validation_format(client: TestClient) -> None:
    missing = client.get("/does-not-exist")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "NOT_FOUND"
    invalid = client.get("/api/games?page=0")
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_detail_and_not_found(client: TestClient) -> None:
    listing = client.get("/api/games?page_size=5&genre=RPG&sort_by=rating&sort_direction=desc")
    assert listing.status_code == 200
    data = listing.json()
    assert data["success"] is True and len(data["items"]) <= 5
    assert data["pagination"]["page_size"] == 5
    game_id = data["items"][0]["id"]
    assert client.get(f"/api/games/{game_id}").json()["item"]["id"] == game_id
    not_found = client.get("/api/games/not-present")
    assert not_found.status_code == 404 and not_found.json()["error"]["code"] == "GAME_NOT_FOUND"


def test_search_and_empty_query(client: TestClient) -> None:
    response = client.get("/api/games/search?q=star&page_size=2")
    assert response.status_code == 200 and response.json()["pagination"]["total_items"] >= 1
    empty = client.get("/api/games/search?q=%20%20")
    assert empty.status_code == 400 and empty.json()["error"]["code"] == "INVALID_QUERY"


def test_facets_and_empty_results(client: TestClient) -> None:
    assert client.get("/api/genres").json()["items"]
    assert client.get("/api/platforms").json()["items"]
    empty = client.get("/api/games?developer=Nobody")
    assert empty.status_code == 200
    assert empty.json()["items"] == [] and empty.json()["pagination"]["total_pages"] == 0


def test_invalid_parameters(client: TestClient) -> None:
    assert client.get("/api/games?page_size=101").status_code == 422
    assert client.get("/api/games?min_rating=9").status_code == 422
    assert client.get("/api/games?sort_by=nope").status_code == 422


def test_pagination_uses_runtime_settings() -> None:
    with TestClient(create_app(Settings(default_page_size=2, max_page_size=3))) as configured_client:
        default_response = configured_client.get("/api/games")
        too_large = configured_client.get("/api/games?page_size=4")
    assert default_response.json()["pagination"]["page_size"] == 2
    assert too_large.status_code == 422
    assert too_large.json()["error"]["code"] == "INVALID_PAGE_SIZE"
