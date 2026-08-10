"""AI endpoint and end-to-end discovery integration tests."""

import pytest
from fastapi.testclient import TestClient


def test_interpret_endpoint(client: TestClient) -> None:
    response = client.post("/api/search/interpret", json={"prompt": "A free multiplayer shooter for low-end PC"})
    assert response.status_code == 200
    data = response.json()
    preferences = data["preferences"]
    assert data["prompt"]["normalized"]
    assert preferences["price_type"] == "free" and preferences["platforms"] == ["PC"]
    assert preferences["confidence"] > 0


EVALUATION_PROMPTS = [
    "shooter",
    "racing",
    "puzzle",
    "strategy",
    "simulation",
    "horror",
    "sports",
    "educational",
    "relaxing",
    "low-end PC",
    "multiplayer",
    "free games",
    "single-player",
    "cooperative",
    "fantasy",
    "science-fiction",
    "cyberpunk",
    "family-friendly",
    "difficult games",
    "casual games",
]


@pytest.mark.parametrize("prompt", EVALUATION_PROMPTS)
def test_recommendation_evaluation_prompt(client: TestClient, prompt: str) -> None:
    response = client.post("/api/search/recommend", json={"prompt": prompt, "limit": 5})
    assert response.status_code == 200
    data = response.json()
    scores = [item["score"] for item in data["items"]]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= score <= 1 for score in scores)
    assert all(item["score_breakdown"]["final_score"] == item["score"] for item in data["items"])


def test_end_to_end_discovery_hard_filters(client: TestClient) -> None:
    prompt = "A free futuristic multiplayer shooter for a low-end PC"
    first = client.post("/api/search/recommend", json={"preference_text": prompt})
    second = client.post("/api/search/recommend", json={"preference_text": prompt})
    assert first.status_code == 200 and first.json() == second.json()
    data = first.json()
    assert data["items"]
    for item in data["items"]:
        game = item["game"]
        assert game["price_category"] == "free" and game["multiplayer"] is True and "PC" in game["platforms"]
        assert item["score_breakdown"] and item["explanation"]


def test_generator_endpoint_e2e(client: TestClient) -> None:
    prompt = "Create a difficult cyberpunk space shooter with fast enemies and increasing difficulty"
    response = client.post("/api/generator/interpret", json={"prompt": prompt})
    assert response.status_code == 200
    data = response.json()
    config = data["configuration"]
    assert data["success"] and data["selection"]["template"] == "space_shooter"
    assert config["theme"] == "cyberpunk" and config["difficulty"] == "hard"
    assert config["enemy_speed"] >= 6 and config["difficulty_scaling"] is True
    assert 1 <= config["lives"] <= 5


def test_unsupported_generator_endpoint(client: TestClient) -> None:
    response = client.post("/api/generator/interpret", json={"prompt": "farming simulator"})
    assert response.status_code == 200 and response.json()["success"] is False


@pytest.mark.parametrize(
    ("prompt", "template"),
    [("endless runner with high jumps", "endless_runner"), ("hard maze escape", "maze_escape")],
)
def test_additional_generator_templates_endpoint(client: TestClient, prompt: str, template: str) -> None:
    response = client.post("/api/generator/interpret", json={"prompt": prompt})
    assert response.status_code == 200
    assert response.json()["configuration"]["template"] == template


def test_generator_endpoint_rejects_wrong_template_override(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"prompt": "space shooter", "overrides": {"maze_size": 15}},
    )
    assert response.status_code == 200 and response.json()["success"] is False
    assert response.json()["warnings"][0]["code"] == "TEMPLATE_INCOMPATIBLE_FIELD"
