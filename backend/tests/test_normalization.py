from decimal import Decimal

from app.data.normalization import (
    normalize_genres,
    normalize_platforms,
    normalize_text,
    normalize_title,
    parse_bool,
    parse_date,
    parse_list,
    parse_price,
    parse_rating,
    price_category,
    slugify,
)


def test_text_and_title_normalization() -> None:
    assert normalize_text("  Hello   world ") == "Hello world"
    assert normalize_text(" null ") is None
    assert normalize_title("  Café—Quest! ") == ("Café—Quest!", "cafe quest")
    assert slugify("Café Quest!") == "cafe-quest"


def test_list_parsing_and_deduplication() -> None:
    assert parse_list('["RPG", "Action", "rpg"]') == ["RPG", "Action"]
    assert parse_list("one|two;three") == ["one", "two", "three"]
    assert parse_list({"unsupported": True}) == []


def test_genre_and_platform_aliases() -> None:
    assert normalize_genres("role-playing|RPG|Puzzle") == ["RPG", "Puzzle"]
    assert normalize_platforms("Windows|PS5|Xbox Series S|Switch") == [
        "PC",
        "PlayStation 5",
        "Xbox Series X|S",
        "Nintendo Switch",
    ]


def test_boolean_rating_date_and_price() -> None:
    assert parse_bool("yes") is True
    assert parse_bool("no") is False
    assert parse_bool("maybe") is None
    assert parse_rating(8, 10) == 4
    assert parse_rating(8) is None
    parsed = parse_date("31/12/2023")
    assert parsed is not None and parsed.isoformat() == "2023-12-31"
    assert parse_date("not-a-date") is None
    assert parse_price("$19.99") == Decimal("19.99")
    assert parse_price(-1) is None
    assert price_category(Decimal("0")) == "free"
    assert price_category(None) == "unknown"
