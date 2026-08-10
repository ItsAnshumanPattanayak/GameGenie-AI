"""Sprint 3 Phase 13 generated-game persistence, compatibility, and sharing tests."""

from collections.abc import Generator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.db.base import Base
from app.db.models import GeneratedGame, User
from app.main import create_app

TEST_SECRET = "test-only-secret-key-with-at-least-thirty-two-characters"
PASSWORD = "StrongPass123"


@pytest.fixture
def generated_client() -> Generator[TestClient, None, None]:
    application = create_app(Settings(database_url="sqlite://", auth_secret_key=TEST_SECRET))
    Base.metadata.create_all(application.state.db_engine)
    with TestClient(application) as client:
        yield client


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"name": "Generated Player", "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}


def configuration(template: str) -> dict[str, Any]:
    configs: dict[str, dict[str, Any]] = {
        "space_shooter": {
            "template": "space_shooter",
            "title": "Saved Stars",
            "theme": "space",
            "difficulty": "hard",
            "player_speed": 8,
            "enemy_speed": 6,
            "enemy_spawn_interval": 1.25,
            "lives": 2,
            "difficulty_scaling": True,
        },
        "endless_runner": {
            "template": "endless_runner",
            "title": "Saved Dash",
            "theme": "neon",
            "difficulty": "medium",
            "player_speed": 11,
            "jump_force": 780,
            "obstacle_frequency": 0.8,
            "difficulty_scaling": True,
        },
        "maze_escape": {
            "template": "maze_escape",
            "title": "Saved Maze",
            "theme": "jungle",
            "difficulty": "hard",
            "maze_size": 25,
            "time_limit": 45,
            "obstacle_count": 14,
        },
    }
    return configs[template]


def create_payload(template: str = "space_shooter", **updates: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": configuration(template)["title"],
        "prompt": f"Create a {template.replace('_', ' ')}",
        "template_type": template,
        "configuration": configuration(template),
        "config_version": "1.1",
    }
    payload.update(updates)
    return payload


def create_game(client: TestClient, headers: dict[str, str], template: str = "space_shooter") -> dict[str, Any]:
    response = client.post("/api/generated-games", headers=headers, json=create_payload(template))
    assert response.status_code == 201, response.text
    return response.json()["item"]


@pytest.mark.parametrize("template", ["space_shooter", "endless_runner", "maze_escape"])
def test_create_list_and_reopen_preserve_each_template(generated_client: TestClient, template: str) -> None:
    headers = auth_headers(generated_client, f"{template}@example.com")
    created = create_game(generated_client, headers, template)
    assert created["configuration"] == configuration(template)
    assert created["config_version"] == "1.1"
    assert created["is_public"] is False

    listed = generated_client.get("/api/generated-games", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [created["id"]]

    reopened = generated_client.get(f"/api/generated-games/{created['id']}", headers=headers)
    assert reopened.status_code == 200
    assert reopened.json()["item"]["configuration"] == configuration(template)


def test_update_and_delete_generated_game(generated_client: TestClient) -> None:
    headers = auth_headers(generated_client, "update@example.com")
    created = create_game(generated_client, headers)
    updated_config = {**configuration("space_shooter"), "player_speed": 10, "lives": 4}
    updated = generated_client.put(
        f"/api/generated-games/{created['id']}",
        headers=headers,
        json={"title": "Updated Stars", "configuration": updated_config},
    )
    assert updated.status_code == 200
    assert updated.json()["item"]["title"] == "Updated Stars"
    assert updated.json()["item"]["configuration"]["player_speed"] == 10

    deleted = generated_client.delete(f"/api/generated-games/{created['id']}", headers=headers)
    assert deleted.status_code == 200 and deleted.json()["deleted_id"] == created["id"]
    assert generated_client.get(f"/api/generated-games/{created['id']}", headers=headers).status_code == 404


def test_update_rejects_empty_and_null_changes(generated_client: TestClient) -> None:
    headers = auth_headers(generated_client, "empty-update@example.com")
    created = create_game(generated_client, headers)
    path = f"/api/generated-games/{created['id']}"
    assert generated_client.put(path, headers=headers, json={}).status_code == 422
    assert generated_client.put(path, headers=headers, json={"title": None}).status_code == 422


def test_owner_scope_hides_and_denies_cross_user_operations(generated_client: TestClient) -> None:
    owner = auth_headers(generated_client, "owner-generated@example.com")
    other = auth_headers(generated_client, "other-generated@example.com")
    created = create_game(generated_client, owner)
    path = f"/api/generated-games/{created['id']}"

    assert generated_client.get(path, headers=other).status_code == 404
    assert generated_client.put(path, headers=other, json={"title": "Stolen"}).status_code == 404
    assert generated_client.delete(path, headers=other).status_code == 404
    assert generated_client.post(f"{path}/share", headers=other).status_code == 404
    assert generated_client.post(f"{path}/unshare", headers=other).status_code == 404
    assert generated_client.get("/api/generated-games", headers=other).json()["items"] == []


def test_share_public_fetch_and_unshare_revoke_slug(generated_client: TestClient) -> None:
    headers = auth_headers(generated_client, "sharing@example.com")
    created = create_game(generated_client, headers, "endless_runner")
    shared = generated_client.post(f"/api/generated-games/{created['id']}/share", headers=headers)
    assert shared.status_code == 200
    item = shared.json()["item"]
    assert item["is_public"] is True
    assert len(item["public_slug"]) >= 24

    public = generated_client.get(f"/api/public/generated-games/{item['public_slug']}")
    assert public.status_code == 200
    public_item = public.json()["item"]
    assert public_item["configuration"] == configuration("endless_runner")
    assert "user_id" not in public_item and "email" not in public_item and "prompt" not in public_item

    unshared = generated_client.post(f"/api/generated-games/{created['id']}/unshare", headers=headers)
    assert unshared.status_code == 200
    assert unshared.json()["item"]["is_public"] is False
    assert unshared.json()["item"]["public_slug"] is None
    denied = generated_client.get(f"/api/public/generated-games/{item['public_slug']}")
    assert denied.status_code == 404 and denied.json()["error"]["code"] == "PUBLIC_GAME_NOT_FOUND"


def test_share_slugs_are_unique_and_idempotent(generated_client: TestClient) -> None:
    headers = auth_headers(generated_client, "unique@example.com")
    first = create_game(generated_client, headers)
    second = create_game(generated_client, headers, "maze_escape")
    first_share = generated_client.post(f"/api/generated-games/{first['id']}/share", headers=headers).json()["item"]
    repeated = generated_client.post(f"/api/generated-games/{first['id']}/share", headers=headers).json()["item"]
    second_share = generated_client.post(f"/api/generated-games/{second['id']}/share", headers=headers).json()["item"]
    assert first_share["public_slug"] == repeated["public_slug"]
    assert first_share["public_slug"] != second_share["public_slug"]


def test_private_invalid_and_unknown_public_slugs_are_not_exposed(generated_client: TestClient) -> None:
    headers = auth_headers(generated_client, "private@example.com")
    create_game(generated_client, headers)
    assert generated_client.get("/api/public/generated-games/short").status_code == 404
    assert generated_client.get(f"/api/public/generated-games/{'x' * 32}").status_code == 404


@pytest.mark.parametrize(
    ("payload_update", "error_code"),
    [
        ({"configuration": {**configuration("space_shooter"), "player_speed": 99}}, "INVALID_GAME_CONFIGURATION"),
        (
            {"configuration": {**configuration("space_shooter"), "maze_size": 15}},
            "INVALID_GAME_CONFIGURATION",
        ),
        (
            {"template_type": "space_shooter", "configuration": configuration("maze_escape")},
            "TEMPLATE_CONFIGURATION_MISMATCH",
        ),
    ],
)
def test_invalid_and_wrong_template_configurations_are_rejected(
    generated_client: TestClient, payload_update: dict[str, Any], error_code: str
) -> None:
    headers = auth_headers(generated_client, f"invalid-{error_code}-{len(str(payload_update))}@example.com")
    response = generated_client.post("/api/generated-games", headers=headers, json=create_payload() | payload_update)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == error_code


def test_legacy_configuration_is_defaulted_and_migration_is_signalled(generated_client: TestClient) -> None:
    headers = auth_headers(generated_client, "legacy@example.com")
    legacy = {
        "title": "Legacy Runner",
        "prompt": "runner",
        "template_type": "endless_runner",
        "configuration": {"title": "Legacy Runner", "theme": "city", "difficulty": "easy"},
        "config_version": "1.0",
    }
    response = generated_client.post("/api/generated-games", headers=headers, json=legacy)
    assert response.status_code == 201
    item = response.json()["item"]
    assert item["config_version"] == "1.1"
    assert item["migrated_from_version"] == "1.0"
    assert item["configuration"]["template"] == "endless_runner"
    assert item["configuration"]["player_speed"] == 7
    assert item["configuration"]["jump_force"] == 550


def test_legacy_configuration_is_validated_and_migrated_when_loaded(generated_client: TestClient) -> None:
    headers = auth_headers(generated_client, "legacy-load@example.com")
    factory = cast(Any, generated_client).app.state.db_session_factory
    with factory() as db:
        user_id = db.scalar(select(User.id).where(User.email == "legacy-load@example.com"))
        row = GeneratedGame(
            user_id=user_id,
            title="Legacy Maze",
            prompt="maze",
            template_type="maze_escape",
            configuration={"title": "Legacy Maze", "theme": "mystery", "difficulty": "medium"},
            config_version="1.0",
            is_public=False,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        game_id = row.id

    response = generated_client.get(f"/api/generated-games/{game_id}", headers=headers)
    assert response.status_code == 200
    item = response.json()["item"]
    assert item["config_version"] == "1.1"
    assert item["migrated_from_version"] == "1.0"
    assert item["configuration"]["template"] == "maze_escape"
    assert item["configuration"]["maze_size"] == 15


def test_malformed_stored_configuration_fails_readably_on_load(generated_client: TestClient) -> None:
    headers = auth_headers(generated_client, "malformed-load@example.com")
    factory = cast(Any, generated_client).app.state.db_session_factory
    with factory() as db:
        user_id = db.scalar(select(User.id).where(User.email == "malformed-load@example.com"))
        row = GeneratedGame(
            user_id=user_id,
            title="Broken Runner",
            prompt="runner",
            template_type="endless_runner",
            configuration={"template": "endless_runner", "title": "Broken Runner", "player_speed": 100},
            config_version="1.1",
            is_public=False,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        game_id = row.id

    response = generated_client.get(f"/api/generated-games/{game_id}", headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_GAME_CONFIGURATION"


@pytest.mark.parametrize(
    ("version", "error_code"),
    [("2.0", "UNSUPPORTED_CONFIG_VERSION"), ("version-one", "INVALID_CONFIG_VERSION")],
)
def test_invalid_config_versions_are_readable(generated_client: TestClient, version: str, error_code: str) -> None:
    headers = auth_headers(generated_client, f"version-{error_code}@example.com")
    response = generated_client.post(
        "/api/generated-games", headers=headers, json=create_payload(config_version=version)
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == error_code
