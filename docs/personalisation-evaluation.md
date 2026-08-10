# Personalisation evaluation

## Automated coverage

Phase 12 adds 38 focused backend tests plus API integration coverage. They cover anonymous and empty-profile regressions; every explicit preference category; multiple and removed favourites; all four feedback types; recency; prompt conflicts and overlap reduction; repeated and empty search history; incomplete profiles; reason deduplication; cap and score bounds; ranking movement; and preservation of the Sprint 2 score breakdown.

Frontend coverage verifies that contextual labels render and detailed scoring remains collapsed until requested.

## Representative interpretation

Use the same prompt and catalogue when comparing users:

1. Anonymous request: item order and `score` come only from semantic retrieval and hybrid ranking. `search_id` is null and no personalisation fields are emitted.
2. New authenticated account: item order and scores match anonymous output; only activity persistence adds `search_id`.
3. Account preferring action and PC: matching games can gain preference influence, while nonmatching games can move slightly down. The active prompt still controls hard filters and receives substantially more influence than overlapping stored categories.
4. Established account: a similar favourite, recent positive feedback, or recurring search theme can move close base candidates. A recent `not_relevant` event makes a bounded downward adjustment; an old event has less effect.

A difference is valid only when the response includes `base_score`, signed `personalisation_score`, `final_score`, and the contributing signal map. Reasons must correspond to observed matches and never claim personalisation for an unchanged result.

## Acceptance thresholds

- Anonymous output equals the non-profile `RecommendationService` result.
- Empty authenticated profiles equal anonymous item output.
- `score` remains in 0–1; explanatory `base_score` and `final_score` remain in 0–100.
- Total profile adjustment never exceeds ±20 points.
- Stored-prompt category overlap reduces profile influence to 25%.
- No runtime embedding training or catalogue mutation occurs.

The development catalogue is intentionally small, so this proves bounded behavior and contract correctness rather than production relevance quality. Offline ranking metrics and larger human-labelled datasets remain future work.

## Recorded development comparison

On 2026-08-10, the prompt `something fun` was run against the same 21-game development catalogue. Anonymous top results began with Deep Signal (57.054%), Lumen Trail (56.580%), and Aurora Drift (53.475%). A new account with explicit `action` and `PC` preferences instead ranked Starling Protocol first at 58.128%, a +4.652-point adjustment grounded in both stored categories. Ember League and Iron Comet entered the top five at 55.000%, each with a capped +5.000-point explicit-preference adjustment.

Deep Signal and Lumen Trail still matched PC but not action, so their combined explicit-preference targets were slightly below their strong base scores and produced small adjustments of −0.705 and −0.658 points. This illustrates that personalisation reranks close candidates without discarding the base result: the original base scores remain visible and continue to dominate.
