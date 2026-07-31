# Sprint 2 AI progress — Anshuman scope

Date: 2026-07-31

## Completed

- Central taxonomy (77 values) and 244 alias/self mappings.
- Unicode-safe normalizer; typed preference extraction; stable conflicts; deterministic confidence.
- Sentence Transformer builder, lazy/injectable embedding service, artifact formats, and integrity checks.
- Vectorized semantic retrieval; 30-candidate default; hybrid ranking, weight redistribution, hard filters, score breakdown, and grounded explanations.
- Space-shooter template selection; typed/clamped Phaser configuration; recommendation handoff.
- Three AI endpoints integrated with the existing FastAPI catalogue service without database changes.
- 142 tests pass: prompt interpretation, embedding integrity, semantic retrieval, ranking, hard filters, explanations, 20 evaluation prompts, generator rules, serialization, APIs, and required end-to-end prompts.
- AI architecture, engine, generation, API, evaluation, and this progress report.

## Partial or blocked

- Production embeddings were generated and integrity-checked locally with `sentence-transformers/all-MiniLM-L6-v2`: 21 rows by 384 dimensions. The three generated artifacts and downloaded model cache are intentionally Git-ignored and must be recreated or provisioned in each deployment environment.
- The evaluation report uses actual MiniLM results. Only 7 of 20 prompts reach at least three explicit matches because the 21-game sample lacks sufficient shooter, educational, family, difficulty, hardware, and theme coverage. Automated tests retain deterministic mock/hash embeddings so they require no model download.
- Backend integration uses the existing in-memory `GameService`. Sarbajit's future database adapter must preserve the bulk catalogue interface or inject the game sequence; search-history persistence is intentionally untouched.
- Thomas's frontend was not present in this repository, so only JSON contract serialization was verified. No Phaser gameplay behavior is claimed.

## Follow-up

Install the full requirements, run the embedding build once with network access, retain artifacts in deployment storage, enrich structured game metadata, evaluate MiniLM against labeled judgments, and let the backend/frontend owners wire persistence and UI display using the documented unchanged/additive contracts.
