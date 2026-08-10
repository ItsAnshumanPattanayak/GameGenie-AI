# Multi-template generation

Sprint 3 Phase 8 expands the existing generator without replacing its Sprint 2 prompt-normalization or Space Shooter behavior. The supported set is deliberately limited to three templates.

## Supported templates

- `space_shooter`
- `endless_runner`
- `maze_escape`

No fourth template is registered by the backend schema or frontend runtime.

## Template selection mappings

Selection is deterministic and recognizes direct requests plus reasonable synonyms:

| Prompt wording | Selected template |
|---|---|
| space shooter, alien shooter, spaceship combat | `space_shooter` |
| runner, endless running, obstacle race | `endless_runner` |
| maze, escape labyrinth, find the exit | `maze_escape` |

Additional weak signals can support a selection, but do not by themselves cause an unrelated genre to be presented as fully supported. If multiple templates have the same best score, the selector uses the fixed priority `space_shooter`, `endless_runner`, `maze_escape` and returns an ambiguity warning.

## Unsupported prompt behavior

The selector chooses a closest supported template only when the prompt has a reasonable partial match. That response sets `fallback: true`, returns a `CLOSEST_TEMPLATE` or `AMBIGUOUS_TEMPLATE` warning, and preserves the source text in `original_prompt`.

When no template reasonably matches, the API returns `success: false`, `configuration: null`, and `UNSUPPORTED_TEMPLATE`. The response lists the three playable identifiers and does not claim that the requested unsupported genre is directly supported. Empty prompts also return no selection and no configuration.

## Endless Runner configuration

`EndlessRunnerConfig` contains:

- `template`: always `endless_runner`
- `title`: sanitized display title
- `theme`: visual theme used by the scene
- `difficulty`: `easy`, `medium`, or `hard`
- `player_speed`: automatic forward speed, bounded from 4 to 14
- `jump_force`: jump velocity magnitude, bounded from 300 to 900
- `obstacle_frequency`: seconds between obstacle spawns, bounded from 0.6 to 4.0
- `difficulty_scaling`: whether speed increases during play

Prompts such as `fast runner` raise `player_speed`; `high jumps` raises `jump_force`; `many obstacles` shortens `obstacle_frequency`; and `gets faster` enables `difficulty_scaling`. The Phaser scene consumes the resulting values for distance scoring, jumping, spawn timing, collision challenge, and game-over behavior.

## Maze Escape configuration

`MazeEscapeConfig` contains:

- `template`: always `maze_escape`
- `title`: sanitized display title
- `theme`: visual theme used by the scene
- `difficulty`: `easy`, `medium`, or `hard`
- `maze_size`: odd maze dimension, bounded from 7 to 31
- `time_limit`: countdown duration in seconds, bounded from 20 to 300
- `obstacle_count`: requested obstacle count, bounded from 0 to 20

`Large maze` increases `maze_size`; `short timer` reduces `time_limit`; and `many obstacles` increases `obstacle_count`. Easy and hard rules adjust the maze size, available time, obstacle count, and movement challenge together. The Phaser scene uses the generated dimensions for deterministic maze construction, the timer for lose conditions, and the obstacle count for placement.

## Shared frontend runtime

`frontend/src/games/registry.ts` maps each identifier to a scene factory and the settings supported by that template. `GameHost` and `mountTemplate` provide the common lifecycle:

- clear stale canvas children before mounting;
- instantiate the scene selected by the registry;
- use Phaser FIT scaling and refresh it on browser resize;
- remove the resize listener and call `game.destroy(true)` during cleanup;
- destroy the previous game before a changed configuration mounts;
- keep an equivalent React rerender from mounting a duplicate instance;
- restart completed scenes without creating another React-owned Phaser game.

The Game Studio at `/generator`, saved player at `/play/saved/:id`, and public player at `/shared/:slug` are loaded with `React.lazy`, keeping Phaser out of the main authentication, activity, and saved-library bundle until needed. `/my-games` is the lightweight persistent library.

## Discriminated validation

The backend represents game configuration as a union discriminated by `template`. Each template has its own schema with extra fields forbidden. Template-incompatible fields are rejected: for example, `maze_size` cannot be supplied to `space_shooter`, and Space Shooter enemy fields cannot be supplied to Maze Escape. Numeric overrides are validated and bounded before a configuration reaches the frontend.

## Saved configuration compatibility

Phase 13 stores the validated discriminator and settings with `config_version`. Current records use `1.1`; compatible `1.0` records are validated again on load, preserve existing core gameplay values, and may receive safe schema defaults for missing values. Responses signal this with `migrated_from_version`. Unsupported or malformed versions and template-incompatible stored data are rejected before Phaser mounts. See [generated-games.md](generated-games.md).

## Verification status

The final Phase 8 regression verification recorded:

- 263 backend tests passing;
- 26 frontend tests passing;
- Ruff lint and formatting checks passing;
- MyPy passing;
- TypeScript checking passing;
- the production Vite build passing;
- Space Shooter, Endless Runner, and Maze Escape browser-smoke-tested;
- one Phaser canvas maintained while switching and resizing;
- cleanup verified when navigating away and remount verified after returning;
- an Endless Runner game-over restart verified in the browser;
- unsupported-prompt warning behavior verified in the browser.

Detailed keyboard feel, collision pacing, and complete win/lose flows across the supported browser matrix remain manual release checks. The build also reports a non-failing large-chunk warning for the lazy Phaser bundle.
