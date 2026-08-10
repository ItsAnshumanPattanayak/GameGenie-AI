import { ArrowLeft, Keyboard, RotateCcw, Settings } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import GameCanvas from '../game/GameCanvas';
import type { GeneratorConfig } from '../types';

const fallback: GeneratorConfig = { title: 'Neon Vanguard', prompt: 'An arcade space defense mission.', theme: 'neon', difficulty: 'normal', playerSpeed: 320, fireRate: 230, enemySpeed: 95, enemyCount: 8, lives: 3, sound: true, screenShake: true };

export default function SpaceShooterPage() {
  const [session, setSession] = useState(0);
  const [config] = useState<GeneratorConfig>(() => { try { return { ...fallback, ...JSON.parse(localStorage.getItem('gamegenie-space-config') ?? '{}') }; } catch { return fallback; } });
  return (
    <div className="play-page page-width page-top">
      <div className="play-head"><div><Link to="/generator" className="back-link"><ArrowLeft /> Back to generator</Link><h1>{config.title}</h1><p>{config.theme} theme · {config.difficulty} difficulty</p></div><div><button className="button button-secondary" onClick={() => setSession((value) => value + 1)}><RotateCcw /> Restart</button><Link className="button" to="/generator"><Settings /> Configure</Link></div></div>
      <GameCanvas key={session} config={config} />
      <div className="controls-strip"><span><Keyboard /> Controls</span><p><kbd>WASD</kbd> or <kbd>Arrows</kbd> move</p><p><kbd>Space</kbd> fire</p><p><kbd>P</kbd> pause</p><p><kbd>R</kbd> restart</p></div>
    </div>
  );
}
