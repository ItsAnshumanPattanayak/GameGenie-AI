"""Sprint 3 user-activity ownership, validation, and persistence tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.base import Base
from app.main import create_app

TEST_SECRET = "test-only-secret-key-with-at-least-thirty-two-characters"
PASSWORD = "StrongPass123"


@pytest.fixture
def activity_client() -> Generator[TestClient, None, None]:
    application = create_app(Settings(database_url="sqlite://", auth_secret_key=TEST_SECRET))
    Base.metadata.create_all(application.state.db_engine)
    with TestClient(application) as client:
        yield client


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"name": "Activity Player", "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}


def first_game_id(client: TestClient) -> str:
    response = client.get("/api/games", params={"page_size": 1})
    assert response.status_code == 200
    return response.json()["items"][0]["id"]


def create_search(client: TestClient, headers: dict[str, str], prompt: str = "relaxing puzzle") -> dict[str, object]:
    response = client.post("/api/search/recommend", headers=headers, json={"prompt": prompt, "limit": 3})
    assert response.status_code == 200
    assert response.json()["search_id"]
    return response.json()


def test_list_read_and_delete_owned_history(activity_client: TestClient) -> None:
    headers = auth_headers(activity_client, "history@example.com")
    created = create_search(activity_client, headers)
    search_id = created["search_id"]

    listed = activity_client.get("/api/history/searches", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["items"][0]["query"] == "relaxing puzzle"
    assert listed.json()["items"][0]["result_count"] == len(created["items"])  # type: ignore[arg-type]
    assert listed.json()["items"][0]["extracted_preferences"]

    detail = activity_client.get(f"/api/history/searches/{search_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["item"]["id"] == search_id

    deleted = activity_client.delete(f"/api/history/searches/{search_id}", headers=headers)
    assert deleted.status_code == 200 and deleted.json()["deleted_count"] == 1
    assert activity_client.get(f"/api/history/searches/{search_id}", headers=headers).status_code == 404


def test_delete_all_history_is_scoped_to_current_user(activity_client: TestClient) -> None:
    first = auth_headers(activity_client, "first@example.com")
    second = auth_headers(activity_client, "second@example.com")
    create_search(activity_client, first, "action game")
    create_search(activity_client, first, "strategy game")
    create_search(activity_client, second, "sports game")

    response = activity_client.delete("/api/history/searches", headers=first)
    assert response.status_code == 200 and response.json()["deleted_count"] == 2
    assert activity_client.get("/api/history/searches", headers=first).json()["items"] == []
    assert len(activity_client.get("/api/history/searches", headers=second).json()["items"]) == 1


def test_history_cross_user_access_is_denied(activity_client: TestClient) -> None:
    owner = auth_headers(activity_client, "owner@example.com")
    other = auth_headers(activity_client, "other@example.com")
    search_id = create_search(activity_client, owner)["search_id"]

    assert activity_client.get(f"/api/history/searches/{search_id}", headers=other).status_code == 404
    assert activity_client.delete(f"/api/history/searches/{search_id}", headers=other).status_code == 404


def test_add_duplicate_list_and_remove_favourite(activity_client: TestClient) -> None:
    headers = auth_headers(activity_client, "favourite@example.com")
    game_id = first_game_id(activity_client)

    first = activity_client.post(f"/api/favourites/{game_id}", headers=headers)
    duplicate = activity_client.post(f"/api/favourites/{game_id}", headers=headers)
    assert first.status_code == 200 and first.json()["created"] is True
    assert duplicate.status_code == 200 and duplicate.json()["created"] is False
    favourites = activity_client.get("/api/favourites", headers=headers)
    assert len(favourites.json()["items"]) == 1
    assert favourites.json()["items"][0]["game"]["id"] == game_id

    removed = activity_client.delete(f"/api/favourites/{game_id}", headers=headers)
    assert removed.status_code == 200
    assert activity_client.get("/api/favourites", headers=headers).json()["items"] == []


def test_favourite_ownership_and_invalid_game(activity_client: TestClient) -> None:
    owner = auth_headers(activity_client, "fav-owner@example.com")
    other = auth_headers(activity_client, "fav-other@example.com")
    game_id = first_game_id(activity_client)
    activity_client.post(f"/api/favourites/{game_id}", headers=owner)

    denied = activity_client.delete(f"/api/favourites/{game_id}", headers=other)
    assert denied.status_code == 404
    invalid = activity_client.post("/api/favourites/not-a-game", headers=owner)
    assert invalid.status_code == 404 and invalid.json()["error"]["code"] == "GAME_NOT_FOUND"


def test_feedback_creation_validation_and_ownership(activity_client: TestClient) -> None:
    owner = auth_headers(activity_client, "feedback-owner@example.com")
    other = auth_headers(activity_client, "feedback-other@example.com")
    game_id = first_game_id(activity_client)
    search_id = create_search(activity_client, owner)["search_id"]

    created = activity_client.post(
        "/api/feedback",
        headers=owner,
        json={"game_id": game_id, "search_id": search_id, "feedback_type": "relevant"},
    )
    assert created.status_code == 201
    assert created.json()["item"]["feedback_type"] == "relevant"
    assert len(activity_client.get("/api/feedback", headers=owner).json()["items"]) == 1

    invalid_type = activity_client.post(
        "/api/feedback", headers=owner, json={"game_id": game_id, "feedback_type": "liked"}
    )
    assert invalid_type.status_code == 422
    invalid_game = activity_client.post(
        "/api/feedback", headers=owner, json={"game_id": "missing", "feedback_type": "interested"}
    )
    assert invalid_game.status_code == 404
    cross_user = activity_client.post(
        "/api/feedback",
        headers=other,
        json={"game_id": game_id, "search_id": search_id, "feedback_type": "not_relevant"},
    )
    assert cross_user.status_code == 404


def test_anonymous_recommendation_still_works_without_history(activity_client: TestClient) -> None:
    response = activity_client.post("/api/search/recommend", json={"prompt": "free multiplayer game", "limit": 2})
    assert response.status_code == 200
    assert response.json()["search_id"] is None
    assert response.json()["items"]
    assert activity_client.get("/api/history/searches").status_code == 401
