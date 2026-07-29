from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.game import GameResponse


@pytest.fixture
def sample_games() -> list[GameResponse]:
    return [
        GameResponse(
            id="alpha",
            title="Alpha Quest",
            normalized_title="alpha quest",
            slug="alpha-quest",
            description="A space exploration role-playing story.",
            genres=["RPG"],
            platforms=["PC"],
            developer="North Studio",
            publisher="One",
            release_year=2024,
            rating=4.8,
            tags=["space", "story"],
            multiplayer=False,
            single_player=True,
            price=20,
            price_category="mid-range",
        ),
        GameResponse(
            id="alphabet",
            title="Alphabet Arena",
            normalized_title="alphabet arena",
            slug="alphabet-arena",
            description="Competitive arena battles.",
            genres=["Action"],
            platforms=["PlayStation 5"],
            developer="South Studio",
            publisher="Two",
            release_year=2023,
            rating=4.0,
            tags=["competitive"],
            multiplayer=True,
            single_player=False,
            price=0,
            price_category="free",
        ),
        GameResponse(
            id="quest",
            title="The Alpha Within",
            normalized_title="the alpha within",
            slug="the-alpha-within",
            description="A quiet puzzle journey.",
            genres=["Puzzle"],
            platforms=["PC"],
            developer="North Studio",
            publisher="Two",
            release_year=2022,
            rating=3.5,
            tags=["relaxing"],
            multiplayer=False,
            single_player=True,
            price=8,
            price_category="budget",
        ),
    ]


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(create_app()) as test_client:
        yield test_client
