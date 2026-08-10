export type GameTemplate = 'space_shooter' | 'endless_runner' | 'maze_escape'
export type GameDifficulty = 'easy' | 'medium' | 'hard'

interface BaseGameConfig {
  template: GameTemplate
  title: string
  theme: string
  difficulty: GameDifficulty
}

export interface SpaceShooterConfig extends BaseGameConfig {
  template: 'space_shooter'
  player_speed: number
  enemy_speed: number
  enemy_spawn_interval: number
  lives: number
  difficulty_scaling: boolean
}

export interface EndlessRunnerConfig extends BaseGameConfig {
  template: 'endless_runner'
  player_speed: number
  jump_force: number
  obstacle_frequency: number
  difficulty_scaling: boolean
}

export interface MazeEscapeConfig extends BaseGameConfig {
  template: 'maze_escape'
  maze_size: number
  time_limit: number
  obstacle_count: number
}

export type GameConfiguration = SpaceShooterConfig | EndlessRunnerConfig | MazeEscapeConfig

export interface GeneratorWarning {
  code: string
  message: string
  fields: string[]
}

export interface GeneratorResponse {
  success: boolean
  selection: {
    template: GameTemplate | null
    supported: boolean
    fallback: boolean
    confidence: number
    reason: string
    original_prompt: string | null
    warnings: GeneratorWarning[]
  }
  configuration: GameConfiguration | null
  warnings: GeneratorWarning[]
}

export interface GeneratedGame {
  id: string
  title: string
  prompt: string
  template_type: GameTemplate
  configuration: GameConfiguration
  config_version: string
  migrated_from_version: string | null
  public_slug: string | null
  is_public: boolean
  created_at: string
  updated_at: string
}

export interface PublicGeneratedGame {
  title: string
  template_type: GameTemplate
  configuration: GameConfiguration
  config_version: string
  migrated_from_version: string | null
  public_slug: string
  created_at: string
  updated_at: string
}
