import Phaser from 'phaser'

import type { SpaceShooterConfig } from '../types'
import { BaseGameScene, themeColor, VIEWPORT } from './BaseGameScene'

export class SpaceShooterScene extends BaseGameScene<SpaceShooterConfig> {
  private player!: Phaser.Physics.Arcade.Sprite
  private enemies!: Phaser.Physics.Arcade.Group
  private bullets!: Phaser.Physics.Arcade.Group
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys
  private fireKey!: Phaser.Input.Keyboard.Key
  private scoreText!: Phaser.GameObjects.Text
  private livesText!: Phaser.GameObjects.Text
  private score = 0
  private lives = 3
  private lastEnemy = 0
  private lastShot = 0

  constructor(settings: SpaceShooterConfig) {
    super('space-shooter', settings)
  }

  create(): void {
    this.cameras.main.setBackgroundColor(themeColor(this.settings.theme))
    this.makeTexture('shooter-player', 36, 28, 0x79e6b5)
    this.makeTexture('shooter-enemy', 32, 24, 0xff7272)
    this.makeTexture('shooter-bullet', 6, 16, 0x9eadff)
    this.heading('Move: arrow keys · Fire: space')
    this.player = this.physics.add.sprite(VIEWPORT.width / 2, VIEWPORT.height - 54, 'shooter-player').setCollideWorldBounds(true)
    this.enemies = this.physics.add.group()
    this.bullets = this.physics.add.group({ maxSize: 30 })
    this.cursors = this.input.keyboard!.createCursorKeys()
    this.fireKey = this.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE)
    this.lives = this.settings.lives
    this.scoreText = this.add.text(VIEWPORT.width - 170, 18, 'Score: 0', { color: '#ffffff', fontSize: '18px' })
    this.livesText = this.add.text(VIEWPORT.width - 170, 44, `Lives: ${this.lives}`, { color: '#ffffff', fontSize: '18px' })
    this.physics.add.overlap(this.bullets, this.enemies, this.hitEnemy, undefined, this)
    this.physics.add.overlap(this.player, this.enemies, this.hitPlayer, undefined, this)
  }

  update(time: number): void {
    if (this.ended) return
    const speed = this.settings.player_speed * 42
    this.player.setVelocity(0)
    if (this.cursors.left.isDown) this.player.setVelocityX(-speed)
    if (this.cursors.right.isDown) this.player.setVelocityX(speed)
    if (this.cursors.up.isDown) this.player.setVelocityY(-speed)
    if (this.cursors.down.isDown) this.player.setVelocityY(speed)
    if (this.fireKey.isDown && time - this.lastShot > 190) this.shoot(time)
    const scaling = this.settings.difficulty_scaling ? 1 + time / 90000 : 1
    const spawnDelay = this.settings.enemy_spawn_interval * 1000 / scaling
    if (time - this.lastEnemy >= spawnDelay) this.spawnEnemy(time, scaling)
    this.bullets.children.each(child => { if ((child as Phaser.Physics.Arcade.Sprite).y < -20) child.destroy(); return true })
    this.enemies.children.each(child => {
      const enemy = child as Phaser.Physics.Arcade.Sprite
      if (enemy.y > VIEWPORT.height + 30) { enemy.destroy(); this.loseLife() }
      return true
    })
  }

  private shoot(time: number): void {
    const bullet = this.bullets.get(this.player.x, this.player.y - 24, 'shooter-bullet') as Phaser.Physics.Arcade.Sprite | null
    if (!bullet) return
    bullet.setActive(true).setVisible(true).setVelocityY(-520)
    this.lastShot = time
  }

  private spawnEnemy(time: number, scaling: number): void {
    const x = Phaser.Math.Between(32, VIEWPORT.width - 32)
    const enemy = this.enemies.create(x, -24, 'shooter-enemy') as Phaser.Physics.Arcade.Sprite
    enemy.setVelocityY(this.settings.enemy_speed * 42 * scaling)
    this.lastEnemy = time
  }

  private hitEnemy(bulletObject: object, enemyObject: object): void {
    ;(bulletObject as Phaser.GameObjects.GameObject).destroy(); (enemyObject as Phaser.GameObjects.GameObject).destroy(); this.score += 100
    this.scoreText.setText(`Score: ${this.score}`)
  }

  private hitPlayer(_player: object, enemy: object): void {
    ;(enemy as Phaser.GameObjects.GameObject).destroy(); this.loseLife()
  }

  private loseLife(): void {
    if (this.ended) return
    this.lives -= 1
    this.livesText.setText(`Lives: ${this.lives}`)
    if (this.lives <= 0) this.finish(`Game over · Score ${this.score}`)
  }
}
