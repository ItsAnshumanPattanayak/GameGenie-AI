import Phaser from 'phaser'

import type { GameConfiguration } from '../types'

export const VIEWPORT = { width: 960, height: 540 } as const

export abstract class BaseGameScene<T extends GameConfiguration> extends Phaser.Scene {
  protected readonly settings: T
  protected ended = false

  protected constructor(key: string, settings: T) {
    super(key)
    this.settings = settings
  }

  protected makeTexture(key: string, width: number, height: number, color: number): void {
    if (this.textures.exists(key)) return
    const graphics = this.make.graphics({ x: 0, y: 0 })
    graphics.fillStyle(color, 1).fillRoundedRect(0, 0, width, height, Math.min(width, height) / 4)
    graphics.generateTexture(key, width, height)
    graphics.destroy()
  }

  protected heading(instructions: string): void {
    this.add.text(18, 14, this.settings.title, { color: '#ffffff', fontFamily: 'system-ui', fontSize: '24px', fontStyle: 'bold' }).setDepth(20)
    this.add.text(18, 46, instructions, { color: '#aeb9df', fontFamily: 'system-ui', fontSize: '14px' }).setDepth(20)
  }

  protected finish(message: string): void {
    if (this.ended) return
    this.ended = true
    this.physics.pause()
    this.add.rectangle(VIEWPORT.width / 2, VIEWPORT.height / 2, 460, 170, 0x080b16, .94).setStrokeStyle(2, 0x9eadff).setDepth(50)
    this.add.text(VIEWPORT.width / 2, VIEWPORT.height / 2 - 30, message, { color: '#ffffff', fontFamily: 'system-ui', fontSize: '32px', fontStyle: 'bold', align: 'center' }).setOrigin(.5).setDepth(51)
    this.add.text(VIEWPORT.width / 2, VIEWPORT.height / 2 + 28, 'Press R or click to restart', { color: '#9eadff', fontFamily: 'system-ui', fontSize: '18px' }).setOrigin(.5).setDepth(51)
    this.input.keyboard?.once('keydown-R', () => this.scene.restart())
    this.input.once('pointerdown', () => this.scene.restart())
  }
}

export function themeColor(theme: string): number {
  const colors: Record<string, number> = {
    cyberpunk: 0x28164f,
    futuristic: 0x102b46,
    fantasy: 0x233b2c,
    jungle: 0x173b2b,
    desert: 0x5a3c20,
    neon: 0x31184f,
    mystery: 0x17213b,
    city: 0x17233d,
    space: 0x080b24,
  }
  return colors[theme] ?? 0x10162a
}
