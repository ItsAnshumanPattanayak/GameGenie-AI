# Recommendation engine

## Retrieval and score scale

The query and game vectors are L2-normalized. `SemanticRecommendationEngine` calculates cosine similarity with one matrix operation, converts `[-1, 1]` cosine to the public `[0, 1]` score scale, validates finiteness, removes duplicate IDs, applies the configurable threshold, and sorts by descending score then game ID. It retrieves at most 30 candidates by default; hybrid ranking returns 10 unless the request asks for another valid limit.

The local FastAPI startup uses the deterministic hash fixture so development and tests never download a model. The artifact builder and injectable production service use `sentence-transformers/all-MiniLM-L6-v2`.

## Hybrid ranking

| Component | Weight |
|---|---:|
| semantic | 0.50 |
| genre | 0.15 |
| platform | 0.10 |
| mode | 0.08 |
| theme | 0.035 |
| mood | 0.035 |
| price | 0.04 |
| difficulty | 0.03 |
| hardware | 0.03 |

Semantic is always active. An optional category is active only when the prompt specifies it. Let `A` be active components and `w` the base weights; the effective weight is `w_i / sum(w_j for j in A)`. Inactive components receive zero weight, so an unspecified preference never lowers a game score and division by zero cannot occur.

Set components use requested-value recall: `|requested ∩ available| / |requested|`. Singular components are exact 0 or 1 matches. Every response exposes semantic, genre, platform, mode, theme, mood, price, difficulty, hardware, and final scores on the same 0–1 scale.

## Hard filters and ordering

Only explicit extractor markers trigger hard filters: a requested platform expressed as `for <platform>` or with `only`; free pricing; multiplayer; and offline. Soft language such as `prefer`, `ideally`, `if possible`, or `nice to have` suppresses those optional hard filters. Conflicting free/paid input also does not become a free-only filter. Unknown data cannot pass a strict offline filter. Filtering occurs before final ranking. Stable ordering is final score descending, normalized title ascending, then game ID ascending. Excluded IDs are removed before ranking. The service does not query individual records.

## Explanations

Explanations use only the recorded category intersections for the ranked game. The strongest first four reasons are rendered deterministically with correct one-, two-, or multi-reason grammar. If only semantic similarity is present, the text says so and does not invent a feature.

## Tuning

The current threshold is `0.0` to avoid hiding candidates in the small development catalogue. For production embeddings, evaluate a threshold near `0.35–0.50`, enrich catalogue taxonomy fields, and tune weights against labeled relevance judgments. See [recommendation-evaluation.md](recommendation-evaluation.md).
