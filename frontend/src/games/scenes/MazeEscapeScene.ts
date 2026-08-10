import Phaser from 'phaser'

import type { MazeEscapeConfig } from '../types'
import { BaseGameScene, themeColor, VIEWPORT } from './BaseGameScene'

export function generateMaze(size: number): number[][] {
  if (size < 7 || size > 31 || size % 2 === 0) throw new Error('Maze size must be an odd number between 7 and 31.')
  const grid = Array.from({ length: size }, () => Array<number>(size).fill(1))
  const stack: Array<[number, number]> = [[1, 1]]
  let seed = size * 7919
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 0x100000000 }
  grid[1][1] = 0
  while (stack.length) {
    const [row, column] = stack[stack.length - 1]
    const directions: Array<[number, number]> = [[-2, 0], [2, 0], [0, -2], [0, 2]]
      .map(value => ({ value, order: random() }))
      .sort((left, right) => left.order - right.order)
      .map(item => item.value as [number, number])
    const next = directions.find(([dr, dc]) => {
      const targetRow = row + dr; const targetColumn = column + dc
      return targetRow > 0 && targetRow < size - 1 && targetColumn > 0 && targetColumn < size - 1 && grid[targetRow][targetColumn] === 1
    })
    if (!next) { stack.pop(); continue }
    const [dr, dc] = next
    grid[row + dr / 2][column + dc / 2] = 0
    grid[row + dr][column + dc] = 0
    stack.push([row + dr, column + dc])
  }
  return grid
}

export function mazeObstacleCells(maze: number[][], count: number): Array<[number, number]> {
  const size = maze.length
  const candidates: Array<[number, number]> = []
  for (let row = 1; row < size - 1; row += 1) {
    for (let column = 1; column < size - 1; column += 1) {
      if (maze[row][column] === 0 && !(row === 1 && column === 1) && !(row === size - 2 && column === size - 2)) candidates.push([row, column])
    }
  }
  const selected: Array<[number, number]> = []
  const step = Math.max(1, Math.floor(candidates.length / Math.max(1, count)))
  for (let index = step - 1; index < candidates.length && selected.length < count; index += step) selected.push(candidates[index])
  return selected
}

export class MazeEscapeScene extends BaseGameScene<MazeEscapeConfig> {
  private player!: Phaser.Physics.Arcade.Sprite
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys
  private keys!: Record<'W' | 'A' | 'S' | 'D', Phaser.Input.Keyboard.Key>
  private timerText!: Phaser.GameObjects.Text
  private remaining = 0

  constructor(settings: MazeEscapeConfig) {
    super('maze-escape', settings)
  }

  create(): void {
    this.cameras.main.setBackgroundColor(themeColor(this.settings.theme))
    this.heading('Move: arrow keys / WASD · Reach the green exit before time expires')
    const maze = generateMaze(this.settings.maze_size)
    const tile = Math.max(12, Math.floor(440 / this.settings.maze_size))
    const mazePixels = tile * this.settings.maze_size
    const offsetX = Math.floor((VIEWPORT.width - mazePixels) / 2)
    const offsetY = 78
    this.makeTexture(`maze-wall-${tile}`, tile, tile, 0x39456f)
    this.makeTexture(`maze-player-${tile}`, Math.max(8, tile - 5), Math.max(8, tile - 5), 0x9eadff)
    this.makeTexture(`maze-exit-${tile}`, Math.max(8, tile - 4), Math.max(8, tile - 4), 0x79e6b5)
    this.makeTexture(`maze-obstacle-${tile}`, Math.max(7, tile - 6), Math.max(7, tile - 6), 0xff7272)
    const walls = this.physics.add.staticGroup()
    maze.forEach((row, rowIndex) => row.forEach((cell, columnIndex) => {
      if (cell === 1) walls.create(offsetX + columnIndex * tile + tile / 2, offsetY + rowIndex * tile + tile / 2, `maze-wall-${tile}`)
    }))
    const point = (row: number, column: number) => ({ x: offsetX + column * tile + tile / 2, y: offsetY + row * tile + tile / 2 })
    const start = point(1, 1)
    this.player = this.physics.add.sprite(start.x, start.y, `maze-player-${tile}`).setCollideWorldBounds(true)
    this.physics.add.collider(this.player, walls)
    const exitPoint = point(this.settings.maze_size - 2, this.settings.maze_size - 2)
    const exit = this.physics.add.staticSprite(exitPoint.x, exitPoint.y, `maze-exit-${tile}`)
    this.physics.add.overlap(this.player, exit, () => this.finish(`You escaped with ${this.remaining}s remaining!`))
    const obstacles = this.physics.add.staticGroup()
    mazeObstacleCells(maze, this.settings.obstacle_count).forEach(([row, column]) => {
      const location = point(row, column); obstacles.create(location.x, location.y, `maze-obstacle-${tile}`)
    })
    this.physics.add.collider(this.player, obstacles, () => this.finish('An obstacle caught you'))
    this.cursors = this.input.keyboard!.createCursorKeys()
    this.keys = this.input.keyboard!.addKeys('W,A,S,D') as Record<'W' | 'A' | 'S' | 'D', Phaser.Input.Keyboard.Key>
    this.remaining = this.settings.time_limit
    this.timerText = this.add.text(VIEWPORT.width - 185, 18, `Time: ${this.remaining}s`, { color: '#ffffff', fontSize: '18px' })
    this.time.addEvent({ delay: 1000, loop: true, callback: () => this.tick() })
  }

  update(): void {
    if (this.ended) return
    const speed = this.settings.difficulty === 'easy' ? 175 : this.settings.difficulty === 'hard' ? 215 : 195
    this.player.setVelocity(0)
    if (this.cursors.left.isDown || this.keys.A.isDown) this.player.setVelocityX(-speed)
    if (this.cursors.right.isDown || this.keys.D.isDown) this.player.setVelocityX(speed)
    if (this.cursors.up.isDown || this.keys.W.isDown) this.player.setVelocityY(-speed)
    if (this.cursors.down.isDown || this.keys.S.isDown) this.player.setVelocityY(speed)
    const body = this.player.body as Phaser.Physics.Arcade.Body
    body.velocity.normalize().scale(speed)
  }

  private tick(): void {
    if (this.ended) return
    this.remaining -= 1
    this.timerText.setText(`Time: ${this.remaining}s`)
    if (this.remaining <= 0) this.finish('Time ran out')
  }
}
