# AI architecture

## Flow

`prompt -> PromptNormalizer -> PreferenceExtractor -> EmbeddingService -> SemanticRecommendationEngine -> HybridRankingEngine -> RecommendationExplanationEngine`

The generator branch is `prompt + optional selected game -> TemplateSelector -> GameConfigurationGenerator`. API routes are thin adapters; all behavior remains testable without FastAPI or a browser. Catalogue records are bulk-loaded once through the existing `GameService`. At application startup, a deterministic offline index is built for dependable local operation. Production-quality artifacts are built separately with the Sentence Transformer script.

## Prompt normalization

Normalization applies NFKC Unicode normalization, trims and case-folds matching text, expands a controlled contraction list, converts punctuation to spaces while retaining meaningful hyphens, collapses whitespace, detects aliases longest-phrase-first with word boundaries, replaces matched phrases with canonical values, and removes consecutive duplicate tokens. The response preserves the original prompt, normalized text, tokens, matched source phrases, and unmatched tokens. Null, empty, punctuation-heavy, 2D/3D, co-op, low-end, counts, and overlapping aliases are covered by tests.

## Controlled taxonomy

- Genres (22): action, adventure, role-playing, first-person shooter, third-person shooter, strategy, simulation, puzzle, racing, sports, platformer, horror, survival, battle royale, fighting, stealth, educational, rhythm, sandbox, casual, exploration, music.
- Platforms (8): PC, PlayStation, Xbox, Nintendo Switch, Android, iOS, macOS, Linux.
- Modes (6): single-player, multiplayer, cooperative, competitive, online, offline.
- Themes (17): fantasy, science-fiction, cyberpunk, space, medieval, post-apocalyptic, historical, military, futuristic, farming, zombies, mythology, detective, educational, family-friendly, nature, mystery.
- Moods (10): relaxing, intense, dark, cheerful, atmospheric, scary, emotional, humorous, competitive, adventurous.
- Visual styles (6): realistic, pixel-art, 2D, 3D, cartoon, retro.
- Difficulty (3): easy, medium, hard.
- Hardware (3): low-end, mid-range, high-end.
- Price (2): free, paid.

`taxonomy.py` exposes immutable tuples through a read-only mapping, validation helpers, reverse category lookup, and 244 deterministic aliases (canonical self-mappings included). Aliases cover abbreviations, spelling/hyphen variants, gaming terms, conversational phrases, and phrases such as `free of cost`, `potato pc`, and `play with friends`. No substring replacement occurs inside unrelated words.

## Extraction, conflicts, and confidence

The immutable Pydantic preference schema carries ordered category tuples, single-valued difficulty/price/hardware, session minutes, player count, structured warnings, matched terms, explicit hard-filter names, and confidence in the 0–1 range. Ordering follows taxonomy order and repeated values are removed.

Stable conflict codes are `CONFLICT_PRICE`, `CONFLICT_DIFFICULTY`, `CONFLICT_CONNECTIVITY`, `CONFLICT_MODE`, `CONFLICT_HARDWARE`, and `CONFLICT_PLAYER_COUNT`. Conflicts remain visible and reduce confidence; the first deterministic canonical value is retained in single-valued fields.

Confidence is deterministic: a 0.12 base plus recognized-token ratio (38%), category coverage up to five categories (34%), and up to five phrase matches (16%), minus 0.12 per conflict (maximum 0.36). Empty text is 0; no-category prompts are capped at 0.18 and one-category prompts at 0.58.

## Embeddings

The production model is `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). `SentenceTransformerEmbeddingService` lazy-loads one process-wide model instance per model name, serializes encode calls, normalizes rows, supports injected models, and makes no paid calls. Runtime loading is local-only by default, so a missing cache produces a controlled error rather than a hidden network request. The builder explicitly enables the public model download; cache it before offline deployment. `DeterministicHashEmbeddingService` is an explicitly documented fixture/degraded-local adapter, not a substitute for production quality.

Build artifacts from `backend`:

```powershell
python -m scripts.build_embeddings --batch-size 32
```

The builder uses labeled title, description, genres, platforms, derived modes, tags/themes, and hardware text; missing fields are omitted. Outputs under `data/embeddings/` are `game_embeddings.npy`, `game_ids.json`, and `metadata.json`. Metadata records format version, model, dimension, game count, UTC generation time, source path/SHA-256, batch size, and normalization. Generated artifacts and model caches are ignored by Git. Integrity checks reject missing/corrupt files, non-2D or non-finite matrices, mismatched counts/dimensions, empty or duplicate IDs, and inconsistent metadata.

## Reliability and limitations

Models and matrices are loaded once, similarity is vectorized, catalogue lookup is bulk-mapped, limits are configurable, tie-breaking is deterministic, and errors are controlled. The 21-game development catalogue does not contain complete difficulty, hardware, educational, family-friendly, or shooter metadata, so those queries cannot achieve high catalogue relevance until the backend dataset is enriched. No frontend gameplay was tested or changed.
