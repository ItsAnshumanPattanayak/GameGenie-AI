from fastapi.testclient import TestClient


def test_valid_medium_prompt_returns_config(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "a medium space shooter", "template": "space_shooter"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["template"] == "space_shooter"
    config = body["configuration"]
    assert config["difficulty"] == "medium"
    assert 3 <= config["player_speed"] <= 10
    assert 1 <= config["enemy_speed"] <= 8
    assert 1 <= config["lives"] <= 5
    assert 0.5 <= config["enemy_spawn_interval"] <= 5.0


def test_hard_prompt_adjusts_config(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "a hard difficult brutal shooter", "template": "space_shooter"},
    )
    assert response.status_code == 200
    config = response.json()["configuration"]
    assert config["difficulty"] == "hard"
    assert config["lives"] <= 3
    assert config["difficulty_scaling"] is True


def test_easy_prompt_adjusts_config(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "an easy relaxing casual game", "template": "space_shooter"},
    )
    assert response.status_code == 200
    config = response.json()["configuration"]
    assert config["difficulty"] == "easy"
    assert config["lives"] >= 3


def test_fast_keyword_increases_speed(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "very fast shooter with quick enemies", "template": "space_shooter"},
    )
    assert response.status_code == 200
    config = response.json()["configuration"]
    assert config["player_speed"] >= 7


def test_dense_keyword_reduces_spawn_interval(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "many enemies in waves attacking", "template": "space_shooter"},
    )
    assert response.status_code == 200
    config = response.json()["configuration"]
    assert config["enemy_spawn_interval"] <= 2.0


def test_cyberpunk_theme_detected(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "cyberpunk neon shooter", "template": "space_shooter"},
    )
    assert response.status_code == 200
    assert response.json()["configuration"]["theme"] == "cyberpunk"


def test_alien_theme_detected(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "alien invasion shooter", "template": "space_shooter"},
    )
    assert response.status_code == 200
    assert response.json()["configuration"]["theme"] == "alien"


def test_scaling_keyword_enables_flag(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "a game that gets harder over time", "template": "space_shooter"},
    )
    assert response.status_code == 200
    assert response.json()["configuration"]["difficulty_scaling"] is True


def test_query_too_short_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "hi", "template": "space_shooter"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_query_over_max_length_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "a" * 501, "template": "space_shooter"},
    )
    assert response.status_code == 422


def test_unsupported_template_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "a valid prompt", "template": "racing_game"},
    )
    assert response.status_code == 422


def test_response_has_all_required_fields(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "a fun shooter game", "template": "space_shooter"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) >= {"success", "query", "template", "configuration", "warnings"}
    config = body["configuration"]
    required = {
        "template", "title", "theme", "difficulty",
        "player_speed", "enemy_speed", "enemy_spawn_interval",
        "lives", "difficulty_scaling",
    }
    assert required.issubset(config.keys())


def test_default_theme_when_no_keyword(client: TestClient) -> None:
    response = client.post(
        "/api/generator/interpret",
        json={"query": "a simple game to play", "template": "space_shooter"},
    )
    assert response.status_code == 200
    assert response.json()["configuration"]["theme"] == "space"
