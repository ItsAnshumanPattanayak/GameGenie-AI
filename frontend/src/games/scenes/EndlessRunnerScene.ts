import Phaser from 'phaser'

import type { EndlessRunnerConfig } from '../types'
import { BaseGameScene, themeColor, VIEWPORT } from './BaseGameScene'

export interface RunnerRuntimeSettings {
  movementSpeed: number
  jumpVelocity: number
  obstacleIntervalMs: number
  difficultyScaling: boolean
}

export function runnerRuntimeSettings(config: EndlessRunnerConfig): RunnerRuntimeSettings {
  return {
    movementSpeed: config.player_speed * 48,
    jumpVelocity: -config.jump_force,
    obstacleIntervalMs: config.obstacle_frequency * 1000,
    difficultyScaling: config.difficulty_scaling,
  }
}

export class EndlessRunnerScene extends BaseGameScene<EndlessRunnerConfig> {
  private player!: Phaser.Physics.Arcade.Sprite
  private obstacles!: Phaser.Physics.Arcade.Group
  private jumpKey!: Phaser.Input.Keyboard.Key
  private scoreText!: Phaser.GameObjects.Text
  private lastObstacle = 0
  private startedAt = 0
  private runtime: RunnerRuntimeSettings

  constructor(settings: EndlessRunnerConfig) {
    super('endless-runner', settings)
    this.runtime = runnerRuntimeSettings(settings)
  }

  create(): void {
    this.cameras.main.setBackgroundColor(themeColor(this.settings.theme))
    this.makeTexture('runner-player', 34, 48, 0x79e6b5)
    this.makeTexture('runner-obstacle', 34, 54, 0xff9f6e)
    this.heading('Jump: space / up arrow · Automatic forward movement')
    const ground = this.add.rectangle(VIEWPORT.width / 2, VIEWPORT.height - 36, VIEWPORT.width, 72, 0x29314d)
    this.physics.add.existing(ground, true)
    this.player = this.physics.add.sprite(130, VIEWPORT.height - 96, 'runner-player').setGravityY(1450).setCollideWorldBounds(true)
    this.obstacles = this.physics.add.group({ allowGravity: false, immovable: true })
    this.physics.add.collider(this.player, ground)
    this.physics.add.collider(this.player, this.obstacles, () => this.finish(`Game over · Distance ${this.distance()}m`))
    this.jumpKey = this.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE)
    this.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.UP).on('down', () => this.jump())
    this.scoreText = this.add.text(VIEWPORT.width - 210, 18, 'Distance: 0m', { color: '#ffffff', fontSize: '18px' })
    this.startedAt = this.time.now
  }

  update(time: number): void {
    if (this.ended) return
    if (Phaser.Input.Keyboard.JustDown(this.jumpKey)) this.jump()
    const elapsed = Math.max(0, time - this.startedAt)
    const scale = this.runtime.difficultyScaling ? 1 + elapsed / 60000 : 1
    if (time - this.lastObstacle >= this.runtime.obstacleIntervalMs / scale) this.spawnObstacle(time, scale)
    this.obstacles.children.each(child => {
      const obstacle = child as Phaser.Physics.Arcade.Sprite
      obstacle.setVelocityX(-this.runtime.movementSpeed * scale)
      if (obstacle.x < -40) obstacle.destroy()
      return true
    })
    this.scoreText.setText(`Distance: ${this.distance()}m`)
  }

  private jump(): void {
    const body = this.player.body as Phaser.Physics.Arcade.Body
    if (body.blocked.down || body.touching.down) this.player.setVelocityY(this.runtime.jumpVelocity)
  }

  private spawnObstacle(time: number, scale: number): void {
    const obstacle = this.obstacles.create(VIEWPORT.width + 25, VIEWPORT.height - 90, 'runner-obstacle') as Phaser.Physics.Arcade.Sprite
    obstacle.setVelocityX(-this.runtime.movementSpeed * scale)
    this.lastObstacle = time
  }

  private distance(): number {
    return Math.floor(Math.max(0, this.time.now - this.startedAt) / 1000 * this.settings.player_speed)
  }
}
