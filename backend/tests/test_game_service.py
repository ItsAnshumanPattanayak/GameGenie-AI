import pytest

from app.core.exceptions import GameNotFoundError
from app.schemas.game import GameResponse, GameSearchFilters
from app.services.game_service import GameService


def test_get_and_not_found(sample_games: list[GameResponse]) -> None:
    service = GameService(sample_games)
    assert service.get("alpha").title == "Alpha Quest"
    with pytest.raises(GameNotFoundError):
        service.get("missing")


def test_filters_sorting_and_pagination(sample_games: list[GameResponse]) -> None:
    service = GameService(sample_games)
    items, meta = service.list_games(
        page=1,
        page_size=1,
        sort_by="rating",
        sort_direction="desc",
        filters=GameSearchFilters(platform="PC", single_player=True, min_rating=4),
    )
    assert [item.id for item in items] == ["alpha"]
    assert (meta.total_items, meta.total_pages) == (1, 1)
    items, _ = service.list_games(
        page=1, page_size=10, filters=GameSearchFilters(developer="North Studio", release_year=2022, multiplayer=False)
    )
    assert [item.id for item in items] == ["quest"]


def test_deterministic_order_and_facets(sample_games: list[GameResponse]) -> None:
    service = GameService(list(reversed(sample_games)))
    one, _ = service.list_games(page=1, page_size=10)
    two, _ = service.list_games(page=1, page_size=10)
    assert [g.id for g in one] == [g.id for g in two] == ["alpha", "alphabet", "quest"]
    assert {item.name: item.count for item in service.genres()} == {"Action": 1, "Puzzle": 1, "RPG": 1}
    assert {item.name for item in service.platforms()} == {"PC", "PlayStation 5"}


def test_search_ranking_and_matching(sample_games: list[GameResponse]) -> None:
    service = GameService(sample_games)
    exact, _ = service.search("  ALPHA QUEST ", page=1, page_size=10)
    assert exact[0].id == "alpha"
    prefix, _ = service.search("alpha", page=1, page_size=10)
    assert [game.id for game in prefix][:2] == ["alpha", "alphabet"]
    genre, _ = service.search("rpg", page=1, page_size=10)
    tag, _ = service.search("space", page=1, page_size=10)
    description, _ = service.search("quiet", page=1, page_size=10)
    assert genre[0].id == tag[0].id == "alpha"
    assert description[0].id == "quest"


def test_search_pagination(sample_games: list[GameResponse]) -> None:
    service = GameService(sample_games)
    items, meta = service.search("alpha", page=2, page_size=1)
    assert len(items) == 1 and meta.total_items == 3 and meta.total_pages == 3
