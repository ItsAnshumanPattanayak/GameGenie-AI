"""In-memory catalogue service, replaceable by a future database adapter."""

from __future__ import annotations

from collections import Counter
from typing import Any, Literal

from app.core.exceptions import GameNotFoundError
from app.schemas.common import FacetItem, PaginationMeta
from app.schemas.game import GameResponse, GameSearchFilters

SortDirection = Literal["asc", "desc"]


class GameService:
    def __init__(self, games: list[GameResponse]) -> None:
        self._games = tuple(games)
        self._by_id = {game.id: game for game in games}

    @property
    def count(self) -> int:
        return len(self._games)

    def get(self, game_id: str) -> GameResponse:
        try:
            return self._by_id[game_id]
        except KeyError as exc:
            raise GameNotFoundError() from exc

    def list_games(
        self,
        *,
        page: int,
        page_size: int,
        sort_by: str = "title",
        sort_direction: SortDirection = "asc",
        filters: GameSearchFilters | None = None,
    ) -> tuple[list[GameResponse], PaginationMeta]:
        games = self._filter(self._games, filters or GameSearchFilters())
        reverse = sort_direction == "desc"
        games.sort(key=lambda game: (self._sort_value(game, sort_by), game.normalized_title, game.id), reverse=reverse)
        return self._paginate(games, page, page_size)

    def search(
        self, query: str, *, page: int, page_size: int, filters: GameSearchFilters | None = None
    ) -> tuple[list[GameResponse], PaginationMeta]:
        needle = " ".join(query.casefold().split())
        ranked: list[tuple[int, GameResponse]] = []
        for game in self._filter(self._games, filters or GameSearchFilters()):
            rank = self._search_rank(game, needle)
            if rank is not None:
                ranked.append((rank, game))
        ranked.sort(key=lambda item: (item[0], item[1].normalized_title, item[1].id))
        return self._paginate([game for _, game in ranked], page, page_size)

    def genres(self) -> list[FacetItem]:
        return self._facets("genres")

    def platforms(self) -> list[FacetItem]:
        return self._facets("platforms")

    def statistics(self) -> dict[str, int]:
        return {"games": self.count, "genres": len(self.genres()), "platforms": len(self.platforms())}

    @staticmethod
    def _paginate(games: list[GameResponse], page: int, page_size: int) -> tuple[list[GameResponse], PaginationMeta]:
        start = (page - 1) * page_size
        return games[start : start + page_size], PaginationMeta(page=page, page_size=page_size, total_items=len(games))

    @staticmethod
    def _sort_value(game: GameResponse, field: str) -> Any:
        value = getattr(game, field)
        if value is None:
            return (1, "")
        if isinstance(value, str):
            value = value.casefold()
        return (0, value)

    @staticmethod
    def _contains(values: list[str], expected: str | None) -> bool:
        return expected is None or expected.casefold() in {value.casefold() for value in values}

    def _filter(self, games: tuple[GameResponse, ...], filters: GameSearchFilters) -> list[GameResponse]:
        result = []
        for game in games:
            if (
                not self._contains(game.genres, filters.genre)
                or not self._contains(game.platforms, filters.platform)
                or not self._contains(game.tags, filters.tag)
            ):
                continue
            if filters.developer and (game.developer or "").casefold() != filters.developer.casefold():
                continue
            if filters.publisher and (game.publisher or "").casefold() != filters.publisher.casefold():
                continue
            if filters.release_year is not None and game.release_year != filters.release_year:
                continue
            if filters.min_rating is not None and (game.rating is None or game.rating < filters.min_rating):
                continue
            if filters.multiplayer is not None and game.multiplayer != filters.multiplayer:
                continue
            if filters.single_player is not None and game.single_player != filters.single_player:
                continue
            if filters.price_category is not None and game.price_category != filters.price_category:
                continue
            result.append(game)
        return result

    @staticmethod
    def _search_rank(game: GameResponse, query: str) -> int | None:
        title = game.normalized_title
        if title == query:
            return 0
        if title.startswith(query):
            return 1
        if query in title:
            return 2
        if any(query in item.casefold() for item in [*game.genres, *game.tags]):
            return 3
        if query in (game.developer or "").casefold() or query in (game.publisher or "").casefold():
            return 4
        if query in (game.description or "").casefold():
            return 5
        return None

    def _facets(self, field: str) -> list[FacetItem]:
        counts: Counter[str] = Counter()
        display: dict[str, str] = {}
        for game in self._games:
            for value in getattr(game, field):
                counts[value.casefold()] += 1
                display.setdefault(value.casefold(), value)
        return [FacetItem(name=display[key], count=counts[key]) for key in sorted(counts)]
