"""Prompt normalization and extraction coverage (more than 30 collected cases)."""

import pytest

from app.ai.preference_extractor import PreferenceExtractor
from app.ai.prompt_normalizer import PromptNormalizer
from app.ai.taxonomy import SYNONYMS, TAXONOMY, category_for, is_canonical


@pytest.fixture
def extractor() -> PreferenceExtractor:
    return PreferenceExtractor()


@pytest.mark.parametrize(
    ("prompt", "field", "expected"),
    [
        ("action game", "genres", "action"),
        ("an adventure", "genres", "adventure"),
        ("RPG", "genres", "role-playing"),
        ("FPS", "genres", "first-person shooter"),
        ("TPS", "genres", "third-person shooter"),
        ("brain game", "genres", "puzzle"),
        ("car game", "genres", "racing"),
        ("football game", "genres", "sports"),
        ("for Windows PC", "platforms", "PC"),
        ("on PS5", "platforms", "PlayStation"),
        ("on Xbox One", "platforms", "Xbox"),
        ("Nintendo switch game", "platforms", "Nintendo Switch"),
        ("play with friends", "modes", "multiplayer"),
        ("co-op game", "modes", "cooperative"),
        ("solo game", "modes", "single-player"),
        ("without internet", "modes", "offline"),
        ("sci fi world", "themes", "science-fiction"),
        ("child friendly", "themes", "family-friendly"),
        ("future world", "themes", "futuristic"),
        ("calm game", "moods", "relaxing"),
        ("funny game", "moods", "humorous"),
        ("pixel art", "visual_styles", "pixel-art"),
        ("two dimensional", "visual_styles", "2D"),
        ("3D game", "visual_styles", "3D"),
        ("difficult game", "difficulty", "hard"),
        ("no cost", "price_type", "free"),
        ("premium game", "price_type", "paid"),
        ("potato pc", "hardware_level", "low-end"),
        ("gaming rig", "hardware_level", "high-end"),
    ],
)
def test_category_extraction(extractor: PreferenceExtractor, prompt: str, field: str, expected: str) -> None:
    value = getattr(extractor.extract(prompt), field)
    assert value == expected or expected in value


def test_required_discovery_prompt(extractor: PreferenceExtractor) -> None:
    result = extractor.extract("A free multiplayer shooter for low-end PC")
    assert result.price_type == "free"
    assert result.modes == ("multiplayer",)
    assert result.genres == ("first-person shooter",)
    assert result.platforms == ("PC",)
    assert result.hardware_level == "low-end"
    assert set(result.hard_filters) == {"free", "multiplayer", "platform"}
    assert result.confidence >= 0.7


def test_relaxing_solo_farming(extractor: PreferenceExtractor) -> None:
    result = extractor.extract("A relaxing solo farming game")
    assert result.moods == ("relaxing",)
    assert result.modes == ("single-player",)
    assert result.themes == ("farming",)


def test_platformer_boss_prompt(extractor: PreferenceExtractor) -> None:
    result = extractor.extract("A difficult 2D platform game with bosses")
    assert result.difficulty == "hard" and result.visual_styles == ("2D",)
    assert result.genres == ("platformer",)


def test_educational_child_prompt(extractor: PreferenceExtractor) -> None:
    result = extractor.extract("A child-friendly educational puzzle game")
    assert "educational" in result.genres
    assert "educational" in result.themes and "family-friendly" in result.themes
    assert "puzzle" in result.genres


@pytest.mark.parametrize(
    ("prompt", "code"),
    [
        ("A paid free game", "CONFLICT_PRICE"),
        ("easy and hard", "CONFLICT_DIFFICULTY"),
        ("online only and offline only", "CONFLICT_CONNECTIVITY"),
        ("single player only and multiplayer only", "CONFLICT_MODE"),
        ("low spec and extreme hardware", "CONFLICT_HARDWARE"),
        ("1 player multiplayer", "CONFLICT_PLAYER_COUNT"),
    ],
)
def test_conflicts(extractor: PreferenceExtractor, prompt: str, code: str) -> None:
    assert code in {warning.code for warning in extractor.extract(prompt).warnings}


def test_vague_unknown_empty_and_whitespace_confidence(extractor: PreferenceExtractor) -> None:
    assert extractor.extract("Give me something good").confidence <= 0.2
    assert extractor.extract("flibbertigibbet").genres == ()
    assert extractor.extract(None).confidence == 0
    assert extractor.extract("   ").confidence == 0


def test_player_count_and_session_length(extractor: PreferenceExtractor) -> None:
    result = extractor.extract("co-op for 4 players in 2 hour sessions")
    assert result.player_count == 4 and result.session_length == 120
    assert extractor.extract("a quick session").session_length == 20


def test_stable_order_and_determinism(extractor: PreferenceExtractor) -> None:
    prompt = "puzzle action racing action"
    first = extractor.extract(prompt)
    assert first.genres == ("action", "puzzle", "racing")
    assert first == extractor.extract(prompt)
    assert 0 <= first.confidence <= 1


def test_normalizer_preserves_original_and_handles_punctuation() -> None:
    result = PromptNormalizer().normalize("  CO-OP, 3D!!! low-end PC  ")
    assert result.original.startswith("  CO-OP")
    assert "cooperative" in result.normalized and "3D" in result.normalized and "low-end" in result.normalized
    assert result.matched_phrases


def test_longest_phrase_wins_and_no_false_substring() -> None:
    normalizer = PromptNormalizer()
    long = normalizer.normalize("low-end pc")
    assert any(match.source == "low-end pc" for match in long.matched_phrases)
    assert not normalizer.normalize("rpgmaker uncooperative").matched_phrases


def test_repeated_words_are_deduplicated() -> None:
    assert PromptNormalizer().normalize("chill chill game").normalized.count("relaxing") == 1


def test_taxonomy_is_complete_and_synonyms_exceed_requirement() -> None:
    minimums = {"genres": 20, "platforms": 8, "modes": 6, "themes": 15, "moods": 10, "visual_styles": 6}
    assert all(len(TAXONOMY[name]) >= count for name, count in minimums.items())
    assert len(SYNONYMS) >= 100
    assert is_canonical("platforms", "PC") and category_for("PC") == "platforms"
