import Phaser from 'phaser'

import { getTemplateDefinition } from './registry'
import type { GameConfiguration } from './types'

export interface MountedGame {
  destroy(removeCanvas: boolean): void
  scale: { refresh(): void }
}

export type PhaserFactory = (settings: Phaser.Types.Core.GameConfig) => MountedGame

export function mountTemplate(
  parent: HTMLElement,
  configuration: GameConfiguration,
  createGame: PhaserFactory = settings => new Phaser.Game(settings),
): () => void {
  if (parent.childElementCount) parent.replaceChildren()
  const definition = getTemplateDefinition(configuration.template)
  const game = createGame({
    type: Phaser.AUTO,
    parent,
    width: 960,
    height: 540,
    backgroundColor: '#080b16',
    physics: { default: 'arcade', arcade: { gravity: { x: 0, y: 0 }, debug: false } },
    scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
    scene: [definition.createScene(configuration)],
    render: { antialias: true, pixelArt: false },
  })
  const resize = () => game.scale.refresh()
  window.addEventListener('resize', resize)
  return () => {
    window.removeEventListener('resize', resize)
    game.destroy(true)
  }
}
