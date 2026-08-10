import { render } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('phaser', () => {
  class Scene {
    sys: { settings: { key: string } }
    constructor(key: string) { this.sys = { settings: { key } } }
  }
  return { default: { Scene, AUTO: 0, Scale: { FIT: 1, CENTER_BOTH: 2 } } }
})

import { GameHost } from '../games/GameHost'
import { getTemplateDefinition, templateRegistry } from '../games/registry'
import { mountTemplate } from '../games/runtime'
import { runnerRuntimeSettings } from '../games/scenes/EndlessRunnerScene'
import { generateMaze, mazeObstacleCells } from '../games/scenes/MazeEscapeScene'
import type { EndlessRunnerConfig, GameConfiguration, MazeEscapeConfig, SpaceShooterConfig } from '../games/types'

const shooter: SpaceShooterConfig = {
  template: 'space_shooter', title: 'Star Defender', theme: 'space', difficulty: 'medium',
  player_speed: 7, enemy_speed: 4, enemy_spawn_interval: 2, lives: 3, difficulty_scaling: false,
}
const runner: EndlessRunnerConfig = {
  template: 'endless_runner', title: 'Neon Dash', theme: 'city', difficulty: 'medium',
  player_speed: 7, jump_force: 550, obstacle_frequency: 2, difficulty_scaling: false,
}
const maze: MazeEscapeConfig = {
  template: 'maze_escape', title: 'Maze Escape', theme: 'mystery', difficulty: 'medium',
  maze_size: 15, time_limit: 90, obstacle_count: 5,
}

describe('multi-template Phaser architecture', () => {
  it('registers exactly the three supported templates', () => {
    expect(Object.keys(templateRegistry)).toEqual(['space_shooter', 'endless_runner', 'maze_escape'])
  })

  it.each<GameConfiguration>([shooter, runner, maze])('dispatches $template through the shared registry', configuration => {
    const scene = getTemplateDefinition(configuration.template).createScene(configuration)
    expect(scene.sys.settings.key).toContain(configuration.template.split('_')[0])
  })

  it('keeps Space Shooter settings available in the shared registry', () => {
    expect(getTemplateDefinition('space_shooter').supportedSettings).toEqual(expect.arrayContaining(['enemy_speed', 'lives', 'enemy_spawn_interval']))
  })

  it('maps runner configuration values to deterministic gameplay settings', () => {
    const baseline = runnerRuntimeSettings(runner)
    const changed = runnerRuntimeSettings({ ...runner, player_speed: 12, jump_force: 850, obstacle_frequency: .7, difficulty_scaling: true })
    expect(changed.movementSpeed).toBeGreaterThan(baseline.movementSpeed)
    expect(changed.jumpVelocity).toBeLessThan(baseline.jumpVelocity)
    expect(changed.obstacleIntervalMs).toBeLessThan(baseline.obstacleIntervalMs)
    expect(changed.difficultyScaling).toBe(true)
  })

  it('generates a deterministic bounded maze with reachable carved cells', () => {
    const first = generateMaze(15)
    expect(first).toEqual(generateMaze(15))
    expect(first).toHaveLength(15)
    expect(first[1][1]).toBe(0)
    expect(first[13][13]).toBe(0)
  })

  it('places the configured number of maze obstacles away from start and exit', () => {
    const cells = mazeObstacleCells(generateMaze(15), 8)
    expect(cells).toHaveLength(8)
    expect(cells).not.toContainEqual([1, 1])
    expect(cells).not.toContainEqual([13, 13])
  })

  it('rejects invalid maze sizes in deterministic scene logic', () => {
    expect(() => generateMaze(10)).toThrow('odd number')
    expect(() => generateMaze(33)).toThrow('between 7 and 31')
  })

  it('shares resize subscription and Phaser destruction in one mount function', () => {
    const destroy = vi.fn()
    const refresh = vi.fn()
    const add = vi.spyOn(window, 'addEventListener')
    const remove = vi.spyOn(window, 'removeEventListener')
    const cleanup = mountTemplate(document.createElement('div'), runner, () => ({ destroy, scale: { refresh } }))
    expect(add).toHaveBeenCalledWith('resize', expect.any(Function))
    window.dispatchEvent(new Event('resize'))
    expect(refresh).toHaveBeenCalledOnce()
    cleanup()
    expect(remove).toHaveBeenCalledWith('resize', expect.any(Function))
    expect(destroy).toHaveBeenCalledWith(true)
  })

  it('does not remount on an equivalent React configuration rerender', () => {
    const cleanup = vi.fn()
    const mount = vi.fn(() => cleanup)
    const view = render(<GameHost configuration={runner} mount={mount} />)
    view.rerender(<GameHost configuration={{ ...runner }} mount={mount} />)
    expect(mount).toHaveBeenCalledOnce()
    expect(cleanup).not.toHaveBeenCalled()
    view.rerender(<GameHost configuration={{ ...runner, player_speed: 9 }} mount={mount} />)
    expect(cleanup).toHaveBeenCalledOnce()
    expect(mount).toHaveBeenCalledTimes(2)
    view.unmount()
    expect(cleanup).toHaveBeenCalledTimes(2)
  })
})
