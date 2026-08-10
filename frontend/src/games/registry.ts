import Phaser from 'phaser'

import { EndlessRunnerScene } from './scenes/EndlessRunnerScene'
import { MazeEscapeScene } from './scenes/MazeEscapeScene'
import { SpaceShooterScene } from './scenes/SpaceShooterScene'
import type { GameConfiguration, GameTemplate } from './types'

export interface TemplateDefinition {
  createScene(config: GameConfiguration): Phaser.Scene
  supportedSettings: readonly string[]
}

export const templateRegistry: Record<GameTemplate, TemplateDefinition> = {
  space_shooter: {
    createScene: config => {
      if (config.template !== 'space_shooter') throw new Error('Space Shooter received incompatible configuration.')
      return new SpaceShooterScene(config)
    },
    supportedSettings: ['title', 'theme', 'difficulty', 'player_speed', 'enemy_speed', 'enemy_spawn_interval', 'lives', 'difficulty_scaling'],
  },
  endless_runner: {
    createScene: config => {
      if (config.template !== 'endless_runner') throw new Error('Endless Runner received incompatible configuration.')
      return new EndlessRunnerScene(config)
    },
    supportedSettings: ['title', 'theme', 'difficulty', 'player_speed', 'jump_force', 'obstacle_frequency', 'difficulty_scaling'],
  },
  maze_escape: {
    createScene: config => {
      if (config.template !== 'maze_escape') throw new Error('Maze Escape received incompatible configuration.')
      return new MazeEscapeScene(config)
    },
    supportedSettings: ['title', 'theme', 'difficulty', 'maze_size', 'time_limit', 'obstacle_count'],
  },
}

export function getTemplateDefinition(template: GameTemplate): TemplateDefinition {
  return templateRegistry[template]
}
