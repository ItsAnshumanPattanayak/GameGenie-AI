"""Reusable embedding models, deterministic game text, and artifact integrity checks."""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol, cast

import numpy as np
from numpy.typing import NDArray

from app.schemas.game import GameResponse

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_FORMAT_VERSION = 1


class EmbeddingError(RuntimeError):
    """Controlled embedding model or artifact failure."""


class Encoder(Protocol):
    def encode(self, sentences: Sequence[str], **kwargs: Any) -> Any: ...


def build_game_text(game: GameResponse) -> str:
    """Create deterministic labeled semantic text while omitting empty values."""
    fields: tuple[tuple[str, object], ...] = (
        ("Title", game.title),
        ("Description", game.description),
        ("Genres", game.genres),
        ("Platforms", game.platforms),
        ("Modes", _game_modes(game)),
        ("Themes and tags", game.tags),
        ("Hardware", game.minimum_requirements),
    )
    parts: list[str] = []
    for label, value in fields:
        if isinstance(value, (list, tuple)):
            clean = [str(item).strip() for item in value if str(item).strip()]
            if clean:
                parts.append(f"{label}: {', '.join(clean)}")
        elif value is not None and str(value).strip():
            parts.append(f"{label}: {str(value).strip()}")
    return ". ".join(parts)


def _game_modes(game: GameResponse) -> list[str]:
    modes: list[str] = []
    if game.single_player:
        modes.append("single-player")
    if game.multiplayer:
        modes.append("multiplayer")
    if game.online_multiplayer:
        modes.append("online")
    if game.multiplayer and any(tag.casefold() in {"co-op", "coop", "cooperative"} for tag in game.tags):
        modes.append("cooperative")
    return modes


class SentenceTransformerEmbeddingService:
    """Thread-safe lazy wrapper that loads one Sentence Transformer per model name."""

    _models: dict[str, Encoder] = {}
    _registry_lock = threading.Lock()

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        model: Encoder | None = None,
        *,
        local_files_only: bool = True,
    ) -> None:
        self.model_name = model_name
        self._injected_model = model
        self.local_files_only = local_files_only
        self._encode_lock = threading.Lock()

    @property
    def ready(self) -> bool:
        return self._injected_model is not None or self.model_name in self._models

    def _model(self) -> Encoder:
        if self._injected_model is not None:
            return self._injected_model
        with self._registry_lock:
            if self.model_name not in self._models:
                try:
                    module = importlib.import_module("sentence_transformers")
                    model_class = vars(module)["SentenceTransformer"]
                    self._models[self.model_name] = cast(
                        Encoder, model_class(self.model_name, local_files_only=self.local_files_only)
                    )
                except Exception as exc:
                    raise EmbeddingError(
                        f"Unable to load embedding model '{self.model_name}'. "
                        "Install sentence-transformers and cache the model."
                    ) from exc
            return self._models[self.model_name]

    def embed(self, texts: Sequence[str], *, batch_size: int = 32) -> NDArray[np.float32]:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        clean = [text.strip() or "Untitled game" for text in texts]
        try:
            with self._encode_lock:
                values = self._model().encode(
                    clean,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )
        except EmbeddingError:
            raise
        except Exception as exc:
            raise EmbeddingError("Embedding encoding failed.") from exc
        matrix = np.asarray(values, dtype=np.float32)
        if matrix.ndim == 1:
            matrix = matrix.reshape(1, -1)
        _validate_matrix(matrix)
        return _normalize_rows(matrix)

    def embed_query(self, query: str) -> NDArray[np.float32]:
        if not query.strip():
            raise EmbeddingError("Query cannot be empty.")
        return self.embed([query])[0]

    def embed_games(self, games: Sequence[GameResponse], *, batch_size: int = 32) -> NDArray[np.float32]:
        return self.embed([build_game_text(game) for game in games], batch_size=batch_size)


class DeterministicHashEmbeddingService:
    """Offline dependency-injection fallback used for tests and degraded local operation."""

    def __init__(self, dimension: int = 384) -> None:
        if dimension < 16:
            raise ValueError("dimension must be at least 16")
        self.dimension = dimension
        self.model_name = f"deterministic-hash-v1-{dimension}"

    @property
    def ready(self) -> bool:
        return True

    def embed(self, texts: Sequence[str], *, batch_size: int = 32) -> NDArray[np.float32]:
        del batch_size
        matrix = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = [token for token in _tokens(text) if len(token) > 1]
            features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:], strict=False)]
            for feature in features:
                digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
                value = int.from_bytes(digest, "little")
                matrix[row, value % self.dimension] += 1.0 if value & 1 else -1.0
        return _normalize_rows(matrix)

    def embed_query(self, query: str) -> NDArray[np.float32]:
        if not query.strip():
            raise EmbeddingError("Query cannot be empty.")
        return self.embed([query])[0]

    def embed_games(self, games: Sequence[GameResponse], *, batch_size: int = 32) -> NDArray[np.float32]:
        return self.embed([build_game_text(game) for game in games], batch_size=batch_size)


def _tokens(text: str) -> list[str]:
    import re

    return re.findall(r"[a-z0-9]+", text.casefold())


def _normalize_rows(matrix: NDArray[np.float32]) -> NDArray[np.float32]:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return np.divide(matrix, norms, out=np.zeros_like(matrix), where=norms != 0)


def _validate_matrix(matrix: NDArray[np.float32]) -> None:
    if matrix.ndim != 2:
        raise EmbeddingError("Embeddings must be a two-dimensional matrix.")
    if matrix.shape[1] == 0:
        raise EmbeddingError("Embedding dimension must be non-zero.")
    if not np.isfinite(matrix).all():
        raise EmbeddingError("Embeddings contain NaN or infinite values.")


class EmbeddingStore:
    """Load and validate an embedding matrix and its row metadata exactly once."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self._lock = threading.Lock()
        self._embeddings: NDArray[np.float32] | None = None
        self._game_ids: tuple[str, ...] | None = None
        self._metadata: dict[str, Any] | None = None

    @property
    def loaded(self) -> bool:
        return self._embeddings is not None

    def load(self) -> tuple[NDArray[np.float32], tuple[str, ...], dict[str, Any]]:
        with self._lock:
            if self._embeddings is not None and self._game_ids is not None and self._metadata is not None:
                return self._embeddings, self._game_ids, dict(self._metadata)
            embedding_path = self.directory / "game_embeddings.npy"
            ids_path = self.directory / "game_ids.json"
            metadata_path = self.directory / "metadata.json"
            missing = [path.name for path in (embedding_path, ids_path, metadata_path) if not path.is_file()]
            if missing:
                raise EmbeddingError(f"Missing embedding files: {', '.join(missing)}")
            try:
                matrix = np.asarray(np.load(embedding_path, allow_pickle=False), dtype=np.float32)
                ids_value = json.loads(ids_path.read_text(encoding="utf-8"))
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                raise EmbeddingError("Embedding files are corrupted or unreadable.") from exc
            if not isinstance(ids_value, list) or not all(isinstance(value, str) for value in ids_value):
                raise EmbeddingError("game_ids.json must contain a JSON array of strings.")
            if not isinstance(metadata, dict):
                raise EmbeddingError("metadata.json must contain a JSON object.")
            ids = tuple(ids_value)
            validate_embedding_artifacts(matrix, ids, metadata)
            self._embeddings, self._game_ids, self._metadata = matrix, ids, metadata
            return matrix, ids, dict(metadata)


def validate_embedding_artifacts(
    matrix: NDArray[np.float32], game_ids: Sequence[str], metadata: dict[str, Any]
) -> None:
    _validate_matrix(matrix)
    if matrix.shape[0] != len(game_ids):
        raise EmbeddingError("Game ID count does not equal embedding row count.")
    if any(not game_id.strip() for game_id in game_ids):
        raise EmbeddingError("Game IDs must be non-empty.")
    if len(set(game_ids)) != len(game_ids):
        raise EmbeddingError("Duplicate game IDs are not allowed.")
    if metadata.get("game_count") != len(game_ids):
        raise EmbeddingError("Metadata game_count is inconsistent.")
    if metadata.get("embedding_dimension") != matrix.shape[1]:
        raise EmbeddingError("Metadata embedding_dimension is inconsistent.")
    if not all(math.isfinite(float(value)) for value in matrix.flat):
        raise EmbeddingError("Embeddings contain non-finite values.")
