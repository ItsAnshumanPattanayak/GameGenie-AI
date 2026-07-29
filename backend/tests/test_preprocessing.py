import json
from pathlib import Path

from app.data.loader import load_raw_records
from app.data.preprocessing import clean_record, merge_games, preprocess_records, run_preprocessing, stable_game_id
from app.schemas.game import GameResponse


def test_alias_mapping_and_cleaning() -> None:
    game = clean_record(
        {
            "name": " Alias Game ",
            "summary": " Test ",
            "genre": "rpg",
            "platform": "windows",
            "score": 4.5,
            "released": "2024-01-02",
            "company": "Studio",
        }
    )
    assert game is not None
    assert (game.title, game.genres, game.platforms, game.release_year) == ("Alias Game", ["RPG"], ["PC"], 2024)


def test_stable_id_is_repeatable() -> None:
    record = {"normalized_title": "same", "release_year": 2020, "developer": "Dev"}
    assert stable_game_id(record) == stable_game_id(record)
    assert stable_game_id({"source": "Sample", "source_id": "42"}) == "sample-42"


def test_malformed_row_does_not_stop_pipeline() -> None:
    games, stats = preprocess_records([{"title": "Valid"}, {"rating": 10}, {"title": "Valid", "genres": "Puzzle"}])
    assert len(games) == 1
    assert stats.skipped_records == 1
    assert stats.duplicate_records == 1
    assert games[0].genres == ["Puzzle"]


def test_duplicate_merge_prefers_complete_and_merges_lists() -> None:
    left = GameResponse(
        id="x", title="Same", normalized_title="same", slug="same", genres=["RPG"], release_year=2020, developer="Dev"
    )
    right = GameResponse(
        id="y",
        title="Same",
        normalized_title="same",
        slug="same",
        genres=["Action"],
        platforms=["PC"],
        release_year=2020,
        developer="Dev",
        description="More",
    )
    merged = merge_games(left, right)
    assert merged.genres == ["Action", "RPG"]
    assert merged.platforms == ["PC"]


def test_loader_valid_missing_and_malformed(tmp_path: Path) -> None:
    valid = tmp_path / "valid.json"
    valid.write_text('{"games": [{"title": "One"}]}', encoding="utf-8")
    assert load_raw_records(valid) == [{"title": "One"}]
    import pytest

    from app.core.exceptions import DatasetMissingError, InvalidDatasetError

    with pytest.raises(DatasetMissingError):
        load_raw_records(tmp_path / "missing.json")
    broken = tmp_path / "broken.json"
    broken.write_text("{oops", encoding="utf-8")
    with pytest.raises(InvalidDatasetError):
        load_raw_records(broken)


def test_deterministic_processed_games(tmp_path: Path) -> None:
    raw = tmp_path / "raw.json"
    out = tmp_path / "processed.json"
    raw.write_text(json.dumps([{"title": "Zulu"}, {"title": "Alpha"}]), encoding="utf-8")
    first, _ = run_preprocessing(raw, out)
    first_output = out.read_bytes()
    second, _ = run_preprocessing(raw, out)
    assert [game.id for game in first] == [game.id for game in second]
    assert [game.title for game in second] == ["Alpha", "Zulu"]
    assert out.read_bytes() == first_output
    assert json.loads(out.read_text(encoding="utf-8"))["games"][0]["title"] == "Alpha"
