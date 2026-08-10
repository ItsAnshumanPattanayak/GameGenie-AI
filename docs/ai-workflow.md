# AI workflow

## Recommendation request

1. Normalize the prompt and extract controlled preferences.
2. Embed the prompt with the existing configured embedding service.
3. Retrieve semantic candidates from the existing in-memory embedding matrix.
4. Apply exclusions, hard filters, active-weight hybrid scoring, and Sprint 2 explanations.
5. For an authenticated user, assemble a bounded profile from preferences, favourites, feedback, and recent searches.
6. Rerank the wider candidate set with capped profile signals, then return the requested limit.
7. Persist the authenticated query and its extracted preferences as search history.

Anonymous requests skip steps 5 and 7 and return the original ranking path unchanged. Empty profiles also bypass reranking.

## Data boundaries

The JSON-backed `GameService` remains the catalogue owner. SQLAlchemy stores accounts and activity using stable game IDs; it does not duplicate catalogue rows. The profile builder performs bounded set queries, and the reranker uses the recommendation service's loaded game map and taxonomy profiles, avoiding N+1 catalogue access.

Generated-game activity is represented as an optional empty profile field until a persistent generated-game model exists. The recommender does not require that future source.

## Explanation boundary

`explanation` and `score_breakdown` continue to describe the active prompt and Sprint 2 hybrid score. Phase 12 adds separate optional percent-scale fields for profile influence. The frontend presents a short contextual label and keeps numeric detail in a collapsed disclosure.
