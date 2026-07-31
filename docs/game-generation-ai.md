# Game-generation AI

## Supported template

`space_shooter` is the only implemented template. Selection requires both a space signal (space, spaceship, starship, or galactic) and a shooting/action signal (shooter, shoot, combat, or blaster). Arcade strengthens confidence. Vague shooters, farming, racing, and empty prompts return a typed unsupported result rather than silently selecting a template.

An optional selected catalogue game is converted to safe descriptive text and joined to the prompt, enabling recommendation-to-generator handoff without coupling generator rules to database access.

## Configuration defaults and rules

Defaults are centralized in `game_generator.py`: title `Star Defender`, theme `space`, medium difficulty, player speed 7, enemy speed 4, spawn interval 2.0 seconds, 3 lives, and difficulty scaling disabled.

Phrase precedence is deterministic: `very fast player` (10) precedes `fast player` (8); `very fast enemies` (7) precedes `fast enemies` (6). `many enemies` uses a 1.0-second interval and `few enemies` uses 4.0. Easy gives 5 lives, enemy speed 2, and a 3.0-second interval. Hard gives 2 lives, enemy speed at least 6, and a 1.25-second interval. `gets harder`, `increasing difficulty`, and `difficulty scaling` enable scaling. Cyberpunk selects the cyberpunk theme and safe title `Cyber Strike`.

## Frontend contract and safety

```json
{
  "template": "space_shooter",
  "title": "Cyber Strike",
  "theme": "cyberpunk",
  "difficulty": "hard",
  "player_speed": 7,
  "enemy_speed": 6,
  "enemy_spawn_interval": 1.25,
  "lives": 2,
  "difficulty_scaling": true
}
```

Limits are player speed 3–10, enemy speed 1–8, spawn interval 0.5–5.0 seconds, and lives 1–5. Numeric overrides are clamped with `VALUE_CLAMPED`; bad types, fields, or difficulty values are ignored with structured warnings. Titles allow only letters, digits, spaces, apostrophes, ampersands, and hyphens, are capped at 60 characters, and return sanitization warnings. Extra executable fields are forbidden by the schema.

This module generates configuration only. It does not implement or claim verification of Phaser movement, collisions, shooting, score, lives, restart, or game-over behavior.

