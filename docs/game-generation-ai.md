# Game-generation AI

GameGenie generates validated configurations for exactly three playable templates:

- `space_shooter`
- `endless_runner`
- `maze_escape`

The backend selects a template and derives bounded settings from a prompt. The frontend then dispatches the returned configuration through a shared Phaser runtime. An optional `selected_game_id` lets catalogue metadata contribute safe descriptive context to the prompt without coupling generator rules to database access.

## Prompt-to-template selection

`TemplateSelector` extends the existing prompt-normalization flow. Direct template names and supported synonyms contribute deterministic scores. Strong mappings include space shooter, alien shooter, and spaceship combat for `space_shooter`; runner, endless running, and obstacle race for `endless_runner`; and maze, escape labyrinth, and find the exit for `maze_escape`.

When multiple templates tie, the selector uses the fixed priority `space_shooter`, `endless_runner`, `maze_escape` and returns `AMBIGUOUS_TEMPLATE`. A partial but reasonable match may select the closest template with `CLOSEST_TEMPLATE`. An unrelated prompt returns `UNSUPPORTED_TEMPLATE`, `success: false`, and no configuration. The selection retains `original_prompt`, so an adaptation never falsely presents an unsupported genre as directly supported.

## Configuration and validation

The API configuration is a Pydantic discriminated union of `SpaceShooterConfig`, `EndlessRunnerConfig`, and `MazeEscapeConfig`, keyed by `template`. Each schema forbids extra fields. A known field from another template, such as `maze_size` on `space_shooter`, produces `TEMPLATE_INCOMPATIBLE_FIELD` and no configuration.

All configurations contain `template`, a sanitized `title`, `theme`, and `difficulty` (`easy`, `medium`, or `hard`). Numeric overrides are kept within schema limits and report `VALUE_CLAMPED` when adjusted. Unknown fields, invalid values, and title sanitization produce structured warnings.

### Space Shooter

Space Shooter retains the Sprint 2 configuration fields `player_speed`, `enemy_speed`, `enemy_spawn_interval`, `lives`, and `difficulty_scaling`. These values control movement, enemy velocity and spawn timing, starting lives, and increasing challenge. The Phaser scene implements movement, firing, enemies, collision, score, game over, and restart.

### Endless Runner

Endless Runner adds `player_speed`, `jump_force`, `obstacle_frequency`, and `difficulty_scaling`. Generated values control automatic forward speed, jump velocity, obstacle interval, and whether speed increases during play. The scene implements jumping, collision, distance scoring, game over, and restart.

### Maze Escape

Maze Escape adds `maze_size`, `time_limit`, and `obstacle_count`, alongside shared difficulty. Generated values control the odd-sized maze dimensions, countdown duration, obstacle placement, and difficulty-adjusted movement. The scene implements deterministic maze generation, movement, an exit, timer, obstacles, win/lose states, and restart.

## Shared Phaser frontend runtime

The protected game studio is available at `/my-games` and `/generator` and is lazy-loaded so Phaser is excluded from the main account/activity bundle. `frontend/src/games/registry.ts` is the single mapping from template identifier to its scene factory and supported settings.

`GameHost` and `mountTemplate` share canvas creation, template dispatch, responsive resize, configuration-change remounting, unmount cleanup, and error display. Before mounting, the host clears stale children. Cleanup removes the resize listener and calls `game.destroy(true)`. Equivalent React rerenders reuse the current mount; a changed configuration destroys the previous instance before mounting another. This prevents duplicate Phaser instances during rerenders, template switching, resizing, and navigation.

Restart behavior is implemented inside the common scene lifecycle: completed games expose restart input and restart their active scene without creating an additional React-owned Phaser instance.

## Catalogue handoff and saved-game compatibility

The implemented compatibility surface is catalogue-to-generator handoff: the frontend may pass a `game` query parameter as `selected_game_id`, and the backend incorporates safe catalogue title, genre, tag, and description text before selection and generation. Unknown catalogue IDs retain the existing game-not-found behavior.

Generated-game persistence and saved play sessions are not implemented. There is therefore no saved-configuration migration or backward-compatibility guarantee yet. Any future saved-game format should retain the `template` discriminator and validate stored data against the matching schema before mounting; incompatible or obsolete fields must not be passed directly to Phaser.

## Known limitations

- Phaser is intentionally lazy-loaded but its production game-studio chunk is large and triggers Vite's chunk-size warning.
- The templates use programmatic shapes and compact mechanics rather than a production asset pipeline, audio system, or content editor.
- Generated games and play progress are not persisted.
- Automated tests cover deterministic configuration and lifecycle logic, while keyboard feel, collision pacing, and visual behavior across browsers still benefit from manual release checks.

See [multi-template-generation.md](multi-template-generation.md) for the template matrix and verified Phase 8 status, and [api-contract.md](api-contract.md) for the HTTP contract.
