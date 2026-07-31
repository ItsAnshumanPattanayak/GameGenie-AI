"""Build versioned Sentence Transformer embedding artifacts for the processed catalogue."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from app.ai.embedding_service import (
    DEFAULT_MODEL_NAME,
    EMBEDDING_FORMAT_VERSION,
    SentenceTransformerEmbeddingService,
    validate_embedding_artifacts,
)
from app.data.loader import load_raw_records
from app.schemas.game import GameResponse

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/games.json"))
    parser.add_argument("--output", type=Path, default=Path("data/embeddings"))
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args()


def _inside_backend(path: Path) -> Path:
    resolved = path if path.is_absolute() else BACKEND_ROOT / path
    resolved = resolved.resolve()
    try:
        resolved.relative_to(BACKEND_ROOT)
    except ValueError as exc:
        raise ValueError("Embedding input and output paths must remain inside backend") from exc
    return resolved


def build(input_path: Path, output_dir: Path, model_name: str, batch_size: int) -> dict[str, object]:
    if batch_size < 1:
        raise ValueError("batch size must be positive")
    source = _inside_backend(input_path)
    output = _inside_backend(output_dir)
    games = [GameResponse.model_validate(item) for item in load_raw_records(source)]
    games.sort(key=lambda game: game.id)
    if not games:
        raise ValueError("The processed catalogue is empty")
    service = SentenceTransformerEmbeddingService(model_name, local_files_only=False)
    matrix = service.embed_games(games, batch_size=batch_size)
    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()
    game_ids = [game.id for game in games]
    metadata: dict[str, object] = {
        "format_version": EMBEDDING_FORMAT_VERSION,
        "model_name": model_name,
        "embedding_dimension": int(matrix.shape[1]),
        "game_count": len(game_ids),
        "generated_at": datetime.now(UTC).isoformat(),
        "source_file": source.relative_to(BACKEND_ROOT).as_posix(),
        "source_sha256": fingerprint,
        "batch_size": batch_size,
        "normalized_embeddings": True,
    }
    validate_embedding_artifacts(matrix, game_ids, metadata)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "game_embeddings.npy").open("wb") as handle:
        np.save(handle, matrix, allow_pickle=False)
    (output / "game_ids.json").write_text(json.dumps(game_ids, indent=2) + "\n", encoding="utf-8")
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    args = _arguments()
    metadata = build(args.input, args.output, args.model, args.batch_size)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
