# Recommendation evaluation

Evaluation date: 2026-07-31. Dataset: `backend/data/processed/games.json`, SHA-256 `c4107c99b911de201b6d761fdc258902ef6ba5be572306600e70339e747c3822`, 21 games. Model: `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions. These are actual outputs from the saved production-model matrix. A result is counted relevant only when its normalized catalogue attributes explicitly satisfy the expected attribute; semantic plausibility alone is not counted.

| Query | Expected | Actual top five | Relevant | Incorrect results | Adjustment required |
|---|---|---|---:|---|---|
| shooter | shooter genre | Starling Protocol; Citadel Zero; Kinetic Kitchen; Iron Comet; Paper Titans | 0 | all 5 | Add shooter-labelled catalogue games |
| racing | racing | Opal Circuit; Aurora Drift; Metro Menders; Kinetic Kitchen; Ember League | 2 | last 3 | Add racing games; tune genre weight |
| puzzle | puzzle | Metro Menders; Harbor Hex; Brass & Bloom; Lumen Trail; Tideglass | 4 | Tideglass | Minor genre-weight tuning |
| strategy | strategy | Paper Titans; Citadel Zero; Harbor Hex; Neon Orchard; Granite Hollow | 5 | none | None for current catalogue |
| simulation | simulation | Metro Menders; Riverbound; Iron Comet; Cloud Gardeners; Granite Hollow | 5 | none | None for current catalogue |
| horror | horror | Deep Signal; Lumen Trail; Fable Archive; Starling Protocol; Quiet Constellation | 1 | last 4 | Add horror games and tune threshold |
| sports | sports | Ember League; Opal Circuit; Paper Titans; Starling Protocol; Jungle Frequency | 1 | last 4 | Add sports games |
| educational | educational | Starling Protocol; Opal Circuit; Kinetic Kitchen; Cloud Gardeners; Paper Titans | 0 | all 5 | Add educational metadata/games |
| relaxing | relaxing mood | Quiet Constellation; Lumen Trail; Harbor Hex; Tideglass; Brass & Bloom | 3 | last 2 | Consider a larger mood weight after more labels |
| low-end PC | PC and low-end | Deep Signal; Iron Comet; Opal Circuit; Granite Hollow; Cloud Gardeners | 0 | all lack hardware evidence | Add structured hardware metadata |
| multiplayer | multiplayer | Iron Comet; Ember League; Paper Titans; Kinetic Kitchen; Opal Circuit | 5 | none | None for current catalogue |
| free games | free | Ember League; Cloud Gardeners | 2 of 2 | none | Catalogue has only two free games |
| single-player | single-player | Starling Protocol; Iron Comet; Paper Titans; Citadel Zero; Opal Circuit | 5 | none | None for current catalogue |
| cooperative | cooperative | Ember League; Kinetic Kitchen; Starling Protocol; Opal Circuit; Paper Titans | 2 | last 3 | Add an explicit co-op field |
| fantasy | fantasy | Ember League; Fable Archive; Paper Titans; Riverbound; Jungle Frequency | 1 | last 4 | Add or label more fantasy titles |
| science-fiction | science-fiction | Starling Protocol; Citadel Zero; Kinetic Kitchen; Paper Titans; Deep Signal | 1 | all except Citadel Zero | Normalize space/sci-fi metadata deliberately |
| cyberpunk | cyberpunk | Starling Protocol; Kinetic Kitchen; Paper Titans; Neon Orchard; Iron Comet | 1 | last 4 | Add cyberpunk titles |
| family-friendly | family-friendly | Quiet Constellation; Kinetic Kitchen; Starling Protocol; Cloud Gardeners; Harbor Hex | 0 | all 5 | Add age/family metadata |
| difficult games | hard difficulty | Paper Titans; Iron Comet; Metro Menders; Ember League; Deep Signal | 0 | all 5 | Add difficulty metadata |
| casual games | casual | Kinetic Kitchen; Cloud Gardeners; Quiet Constellation; Starling Protocol; Metro Menders | 3 | last 2 | Minor genre-weight tuning |

Seven prompts meet at least 3 relevant results in the top five; several others are structurally impossible with this small dataset. The target is therefore not met for most prompts. The automated suite uses deterministic mock/hash embeddings so it remains offline and reproducible; this report separately records the actual MiniLM run. Next steps are to enrich catalogue fields, label a larger relevance set, compare thresholds, and tune weights only against those judgments.
