import Phaser from 'phaser';
import { useEffect, useRef } from 'react';
import type { GeneratorConfig } from '../types';

type Ship = Phaser.Physics.Arcade.Sprite;

class SpaceShooterScene extends Phaser.Scene {
  private settings!: GeneratorConfig;
  private player!: Ship;
  private bullets!: Phaser.Physics.Arcade.Group;
  private enemies!: Phaser.Physics.Arcade.Group;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private keys!: Record<string, Phaser.Input.Keyboard.Key>;
  private scoreText!: Phaser.GameObjects.Text;
  private livesText!: Phaser.GameObjects.Text;
  private waveText!: Phaser.GameObjects.Text;
  private pauseText!: Phaser.GameObjects.Text;
  private nextShotAt = 0;
  private score = 0;
  private lives = 3;
  private wave = 1;
  private remaining = 0;
  private invulnerable = false;
  private ended = false;

  constructor() { super('SpaceShooter'); }

  create() {
    this.settings = this.registry.get('settings') as GeneratorConfig;
    this.lives = this.settings.lives;
    this.createTextures();
    this.createBackdrop();
    this.player = this.physics.add.sprite(480, 465, 'player');
    this.player.setCollideWorldBounds(true).setDepth(5);
    this.player.body!.setSize(34, 34);
    this.bullets = this.physics.add.group({ defaultKey: 'bullet', maxSize: 48 });
    this.enemies = this.physics.add.group();
    this.cursors = this.input.keyboard!.createCursorKeys();
    this.keys = this.input.keyboard!.addKeys('W,A,S,D,SPACE,P,R') as Record<string, Phaser.Input.Keyboard.Key>;
    this.physics.add.overlap(this.bullets, this.enemies, this.hitEnemy as Phaser.Types.Physics.Arcade.ArcadePhysicsCallback, undefined, this);
    this.physics.add.overlap(this.player, this.enemies, this.hitPlayer as Phaser.Types.Physics.Arcade.ArcadePhysicsCallback, undefined, this);
    this.createHud();
    this.spawnWave();
    this.input.on('pointermove', (pointer: Phaser.Input.Pointer) => {
      if (pointer.isDown && pointer.y > 190 && !this.ended) this.player.setPosition(Phaser.Math.Clamp(pointer.x, 26, 934), Phaser.Math.Clamp(pointer.y, 230, 510));
    });
    this.input.on('pointerdown', (pointer: Phaser.Input.Pointer) => { if (pointer.y < 230) this.shoot(this.time.now); });
  }

  update(time: number) {
    if (Phaser.Input.Keyboard.JustDown(this.keys.R)) { this.scene.restart(); return; }
    if (Phaser.Input.Keyboard.JustDown(this.keys.P) && !this.ended) this.setPaused(!this.physics.world.isPaused);
    if (this.ended || this.physics.world.isPaused) return;

    const x = Number(this.cursors.right.isDown || this.keys.D.isDown) - Number(this.cursors.left.isDown || this.keys.A.isDown);
    const y = Number(this.cursors.down.isDown || this.keys.S.isDown) - Number(this.cursors.up.isDown || this.keys.W.isDown);
    const direction = new Phaser.Math.Vector2(x, y).normalize().scale(this.settings.playerSpeed);
    this.player.setVelocity(direction.x, direction.y);
    this.player.setRotation(direction.x * 0.00018);
    if (this.cursors.space.isDown || this.keys.SPACE.isDown) this.shoot(time);

    this.bullets.getChildren().forEach((child) => { const bullet = child as Phaser.Physics.Arcade.Sprite; if (bullet.active && bullet.y < -20) bullet.disableBody(true, true); });
    let breached = 0;
    this.enemies.getChildren().forEach((child) => {
      const enemy = child as Phaser.Physics.Arcade.Sprite;
      if (enemy.active && enemy.y > 570) { enemy.destroy(); this.remaining -= 1; breached += 1; }
    });
    if (breached) this.damagePlayer(breached);
    if (this.remaining <= 0 && !this.ended) { this.wave += 1; this.time.delayedCall(500, () => this.spawnWave()); this.remaining = -999; }
  }

  private createTextures() {
    const make = (key: string, width: number, height: number, draw: (graphics: Phaser.GameObjects.Graphics) => void) => {
      const graphics = this.make.graphics({ x: 0, y: 0 }); draw(graphics); graphics.generateTexture(key, width, height); graphics.destroy();
    };
    make('player', 48, 54, (g) => {
      const accent = this.themeColor();
      g.fillStyle(0x0b1024).fillTriangle(24, 0, 46, 48, 24, 39).fillTriangle(24, 0, 2, 48, 24, 39);
      g.lineStyle(3, accent, 1).strokeTriangle(24, 2, 45, 48, 24, 39).strokeTriangle(24, 2, 3, 48, 24, 39);
      g.fillStyle(0xffffff).fillCircle(24, 26, 4); g.fillStyle(0x43e8d8).fillTriangle(17, 43, 24, 54, 31, 43);
    });
    make('enemy', 46, 36, (g) => {
      g.fillStyle(0x141a31).fillRoundedRect(2, 6, 42, 27, 8); g.lineStyle(2, 0xff4f78).strokeRoundedRect(2, 6, 42, 27, 8);
      g.fillStyle(0xff4f78).fillTriangle(2, 12, 14, 0, 17, 12).fillTriangle(44, 12, 32, 0, 29, 12); g.fillStyle(0xffffff).fillCircle(17, 20, 3).fillCircle(29, 20, 3);
    });
    make('bullet', 8, 24, (g) => { g.fillStyle(0xffffff).fillRoundedRect(2, 0, 4, 20, 2); g.fillStyle(this.themeColor(), 0.8).fillRect(0, 5, 8, 15); });
  }

  private themeColor() {
    return ({ neon: 0x43e8d8, solar: 0xffbf47, frost: 0x72b7ff, mono: 0xffffff } as Record<string, number>)[this.settings?.theme ?? 'neon'] ?? 0x43e8d8;
  }

  private createBackdrop() {
    this.cameras.main.setBackgroundColor('#060814');
    const grid = this.add.graphics().setDepth(-3);
    grid.lineStyle(1, this.themeColor(), 0.08);
    for (let x = 0; x <= 960; x += 64) grid.lineBetween(x, 0, x, 540);
    for (let y = 0; y <= 540; y += 54) grid.lineBetween(0, y, 960, y);
    for (let i = 0; i < 85; i += 1) {
      const star = this.add.circle(Phaser.Math.Between(5, 955), Phaser.Math.Between(5, 535), Phaser.Math.Between(1, 2), i % 9 === 0 ? this.themeColor() : 0xffffff, Phaser.Math.FloatBetween(0.2, 0.75)).setDepth(-2);
      this.tweens.add({ targets: star, alpha: { from: star.alpha, to: 0.05 }, duration: Phaser.Math.Between(700, 1900), yoyo: true, repeat: -1 });
    }
    this.add.rectangle(480, 58, 960, 116, 0x070a16, 0.7).setDepth(-1);
    this.add.rectangle(480, 116, 960, 1, this.themeColor(), 0.3).setDepth(-1);
  }

  private createHud() {
    const text = { fontFamily: 'Arial, sans-serif', color: '#d8def3', fontSize: '18px', fontStyle: 'bold' };
    this.add.text(24, 21, this.settings.title.toUpperCase(), { ...text, color: '#ffffff', fontSize: '16px' });
    this.scoreText = this.add.text(24, 66, 'SCORE 000000', text);
    this.waveText = this.add.text(480, 42, 'WAVE 1', { ...text, color: '#43e8d8', fontSize: '21px' }).setOrigin(0.5);
    this.livesText = this.add.text(936, 66, `LIVES ${this.lives}`, text).setOrigin(1, 0);
    this.add.text(936, 22, this.settings.difficulty.toUpperCase(), { ...text, fontSize: '13px', color: '#8d96b6' }).setOrigin(1, 0);
    this.pauseText = this.add.text(480, 270, '', { fontFamily: 'Arial, sans-serif', fontSize: '38px', color: '#ffffff', fontStyle: 'bold', align: 'center', backgroundColor: '#070914dd', padding: { x: 28, y: 20 } }).setOrigin(0.5).setDepth(20);
  }

  private spawnWave() {
    if (this.ended) return;
    const count = Math.min(22, this.settings.enemyCount + (this.wave - 1) * 2);
    this.remaining = count;
    this.waveText.setText(`WAVE ${this.wave}`);
    const columns = Math.min(8, count);
    for (let i = 0; i < count; i += 1) {
      const x = 120 + (i % columns) * (720 / Math.max(1, columns - 1));
      const y = -60 - Math.floor(i / columns) * 70 - Phaser.Math.Between(0, 25);
      const enemy = this.enemies.create(x, y, 'enemy') as Ship;
      const speedBoost = this.settings.difficulty === 'hard' ? 1.35 : this.settings.difficulty === 'easy' ? 0.75 : 1;
      enemy.setVelocity(Phaser.Math.Between(-30, 30), (this.settings.enemySpeed + this.wave * 7) * speedBoost).setBounce(1, 0).setCollideWorldBounds(true);
      enemy.body!.setSize(38, 28);
      this.tweens.add({ targets: enemy, angle: { from: -4, to: 4 }, duration: 700 + (i % 3) * 180, yoyo: true, repeat: -1 });
    }
  }

  private shoot(time: number) {
    if (time < this.nextShotAt || this.ended) return;
    this.nextShotAt = time + this.settings.fireRate;
    const bullet = this.bullets.get(this.player.x, this.player.y - 26) as Ship | null;
    if (!bullet) return;
    bullet.enableBody(true, this.player.x, this.player.y - 26, true, true).setVelocityY(-610).setDepth(3);
    this.soundEffect(480, 0.025, 'square');
  }

  private hitEnemy(bulletObject: Phaser.GameObjects.GameObject, enemyObject: Phaser.GameObjects.GameObject) {
    const bullet = bulletObject as Ship; const enemy = enemyObject as Ship;
    bullet.disableBody(true, true); this.explode(enemy.x, enemy.y); enemy.destroy();
    this.remaining -= 1; this.score += 100 * this.wave; this.scoreText.setText(`SCORE ${String(this.score).padStart(6, '0')}`);
    this.soundEffect(140, 0.06, 'sawtooth');
  }

  private hitPlayer(_playerObject: Phaser.GameObjects.GameObject, enemyObject: Phaser.GameObjects.GameObject) {
    const enemy = enemyObject as Ship; this.explode(enemy.x, enemy.y); enemy.destroy(); this.remaining -= 1; this.damagePlayer(1);
  }

  private damagePlayer(amount: number) {
    if (this.invulnerable || this.ended) return;
    this.lives = Math.max(0, this.lives - amount); this.livesText.setText(`LIVES ${this.lives}`);
    if (this.settings.screenShake) this.cameras.main.shake(140, 0.006);
    if (this.lives <= 0) { this.endGame(); return; }
    this.invulnerable = true; this.player.setTint(0xff4f78);
    this.tweens.add({ targets: this.player, alpha: 0.25, duration: 100, yoyo: true, repeat: 5, onComplete: () => { this.player.clearTint().setAlpha(1); this.invulnerable = false; } });
  }

  private explode(x: number, y: number) {
    for (let i = 0; i < 12; i += 1) {
      const dot = this.add.circle(x, y, Phaser.Math.Between(2, 5), i % 2 ? this.themeColor() : 0xff4f78).setDepth(9);
      const angle = Phaser.Math.FloatBetween(0, Math.PI * 2); const distance = Phaser.Math.Between(25, 70);
      this.tweens.add({ targets: dot, x: x + Math.cos(angle) * distance, y: y + Math.sin(angle) * distance, alpha: 0, scale: 0.2, duration: Phaser.Math.Between(260, 480), onComplete: () => dot.destroy() });
    }
  }

  private setPaused(paused: boolean) {
    if (paused) { this.physics.pause(); this.pauseText.setText('PAUSED\nP TO RESUME'); }
    else { this.physics.resume(); this.pauseText.setText(''); }
  }

  private endGame() {
    this.ended = true; this.physics.pause(); this.player.setTint(0xff4f78);
    this.pauseText.setText(`MISSION OVER\nSCORE ${this.score}\nPRESS R TO RESTART`);
  }

  private soundEffect(frequency: number, duration: number, type: OscillatorType) {
    if (!this.settings.sound) return;
    try {
      const context = new AudioContext(); const oscillator = context.createOscillator(); const gain = context.createGain();
      oscillator.type = type; oscillator.frequency.value = frequency; gain.gain.setValueAtTime(0.025, context.currentTime); gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + duration);
      oscillator.connect(gain).connect(context.destination); oscillator.start(); oscillator.stop(context.currentTime + duration); oscillator.addEventListener('ended', () => void context.close());
    } catch { /* Audio is a progressive enhancement. */ }
  }
}

export default function GameCanvas({ config }: { config: GeneratorConfig }) {
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!container.current) return;
    const game = new Phaser.Game({
      type: Phaser.AUTO,
      parent: container.current,
      width: 960,
      height: 540,
      backgroundColor: '#060814',
      physics: { default: 'arcade', arcade: { debug: false } },
      scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
      scene: SpaceShooterScene,
      render: { antialias: true, pixelArt: false },
      input: { keyboard: true, mouse: true, touch: true },
    });
    game.registry.set('settings', config);
    return () => game.destroy(true);
  }, [config]);

  return <div className="game-frame"><div ref={container} className="phaser-mount" aria-label={`${config.title} playable game canvas`} /><div className="touch-hint">Drag to move · tap upper field to fire</div></div>;
}
