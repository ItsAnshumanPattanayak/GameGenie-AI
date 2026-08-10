# Personalised recommendation engine

Sprint 3 Phase 12 adds a bounded reranking stage after the existing Sprint 2 semantic retrieval, hard filters, hybrid scoring, and grounded explanation. It does not replace or retrain the base recommender.

## Profile

`PersonalisationProfile` is API-neutral and contains normalized explicit preferences, favourite game IDs, positive and negative feedback IDs, timestamped feedback events, recurring recent-search terms/preferences, and an empty generated-game slot. The database adapter loads each source in a bounded query. Missing generated-game data is not assumed.

Recent searches use at most ten entries from the last 90 days. A controlled value or useful term must recur in at least two searches before it becomes a signal. Feedback loads at most 100 recent records and decays with a 90-day half-life.

## Formula

| Component | Weight |
|---|---:|
| Existing hybrid score | 80% |
| Explicit preferences | 10% |
| Favourite similarity | 4% |
| Recommendation feedback | 4% |
| Recurring recent searches | 2% |

For each available component, the contribution is `weight × (component target − base score)`. Unavailable components are returned to the base score, so anonymous users and empty profiles are exactly unchanged. Feedback first produces a signed, recency-weighted signal and converts it to a bounded target around the base score. With all signals active, the existing hybrid score retains its 80% target.

The summed personalisation delta is capped to ±20 percentage points, then the final value is clamped to 0–100. The legacy `score` remains the same value on its existing 0–1 API scale.

## Controls and signals

- Explicit categories are averaged so adding profile fields cannot multiply the 10% budget. A category present in the active prompt receives only 25% of normal profile influence.
- Favourite similarity uses existing catalogue genres, platforms, modes, tags, themes, and moods. It averages at most the three closest favourites and performs no model training.
- `relevant` and `interested` are positive, `already_played` is mildly positive, and `not_relevant` is negative. Similar-game effects are weaker than direct-game effects. One negative event is capped and cannot remove a whole genre.
- Recent searches only use recurring controlled concepts; one vague or old search contributes nothing.
- Reasons are deterministic, deduplicated, and emitted only when a signal changes the score.

Weights and controls are environment-configurable through the `PERSONALISATION_*` settings in `backend/.env.example`. Values stay in 0–1 and the five component weights must sum to one.

## Cold starts

- Anonymous: exact Sprint 2 ranking and response fields.
- New account with no profile activity: exact Sprint 2 ranking.
- Explicit preferences only: bounded preference reranking.
- Established account: available preference, favourite, feedback, and recurring-search signals participate; absent signals do not penalize the result.

The base `score_breakdown` remains the Sprint 2 breakdown. Optional `base_score`, `personalisation_score`, `final_score`, `personalisation_signals`, and `personalisation_reasons` explain only the Phase 12 adjustment.

Authenticated users submit natural-language discovery prompts from the Dashboard. A recommendation card shows a concise personalisation context only when the response contains reasons for an actual score change; detailed base, adjustment, final score, and reasons remain collapsed by default.
