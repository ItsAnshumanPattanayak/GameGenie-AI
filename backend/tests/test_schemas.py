from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.common import PaginationMeta
from app.schemas.game import GameResponse


def test_valid_game_and_serialization() -> None:
    game = GameResponse(
        id="1",
        title="Test",
        release_date=date(2024, 1, 2),
        rating=4.5,
        price=Decimal("2.50"),
        genres=["RPG"],
        website_url="https://example.com/game",
    )
    data = game.model_dump(mode="json")
    assert data["release_date"] == "2024-01-02"
    assert data["release_year"] == 2024
    assert data["website_url"] == "https://example.com/game"


@pytest.mark.parametrize("field,value", [("rating", 5.1), ("rating", -0.1), ("price", -1)])
def test_invalid_numeric_ranges(field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        GameResponse(id="1", title="Bad", **{field: value})


def test_invalid_url_and_optional_fields() -> None:
    with pytest.raises(ValidationError):
        GameResponse(id="1", title="Bad", website_url="not a url")
    assert GameResponse(id="1", title="Optional", description=" ").description is None


def test_zero_result_pagination() -> None:
    page = PaginationMeta(page=1, page_size=20, total_items=0)
    assert page.total_pages == 0
