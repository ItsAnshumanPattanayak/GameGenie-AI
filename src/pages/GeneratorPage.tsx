import { Braces, Check, Gamepad2, LoaderCircle, RotateCcw, SlidersHorizontal, Sparkles, WandSparkles } from 'lucide-react';
import { FormEvent, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { generateGame } from '../api/gameApi';
import { mockGames } from '../data/mockGames';
import type { GeneratorConfig } from '../types';

const defaults: GeneratorConfig = { title: 'Neon Vanguard', prompt: 'A bold space defense mission with escalating enemy waves and bright arcade energy.', theme: 'neon', difficulty: 'normal', playerSpeed: 320, fireRate: 230, enemySpeed: 95, enemyCount: 8, lives: 3, sound: true, screenShake: true };

export default function GeneratorPage() {
  const [searchParams] = useSearchParams();
  const source = mockGames.find((game) => game.id === searchParams.get('inspiredBy'));
  const initial = source ? { ...defaults, title: `${source.title}: Reimagined`, prompt: `A ${source.tags.slice(0, 2).join(', ').toLowerCase()} space shooter inspired by ${source.title}.` } : defaults;
  const [config, setConfig] = useState<GeneratorConfig>(initial);
  const [status, setStatus] = useState<'idle' | 'generating' | 'ready'>('idle');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const validation = useMemo(() => ({ title: config.title.trim().length >= 3, prompt: config.prompt.trim().length >= 20 }), [config]);
  const valid = validation.title && validation.prompt;
  const update = <K extends keyof GeneratorConfig>(key: K, value: GeneratorConfig[K]) => { setConfig((current) => ({ ...current, [key]: value })); setStatus('idle'); };
  const submit = async (event: FormEvent) => {
    event.preventDefault(); if (!valid) { setError('Add a title and a more detailed prompt before generating.'); return; }
    setError(''); setStatus('generating');
    try { const generated = await generateGame(config); setConfig(generated); localStorage.setItem('gamegenie-space-config', JSON.stringify(generated)); setStatus('ready'); }
    catch { setError('Generation paused unexpectedly. Please try again.'); setStatus('idle'); }
  };
  const play = () => { localStorage.setItem('gamegenie-space-config', JSON.stringify(config)); navigate('/play/space-shooter'); };
  const reset = () => { setConfig(defaults); setStatus('idle'); setError(''); };
  return (
    <div className="page-width page-top generator-page">
      <div className="page-title-row"><div><span className="eyebrow"><WandSparkles size={15} /> Playable game generator</span><h1>Build your Space Shooter</h1><p>Tune the game, inspect the configuration, then launch it instantly.</p></div><div className="generator-status"><span className={status === 'ready' ? 'ready' : ''}>{status === 'ready' ? <Check /> : <Sparkles />}{status === 'ready' ? 'Ready to play' : 'Local preview'}</span></div></div>
      <form className="generator-grid" onSubmit={submit}>
        <section className="generator-main">
          <div className="panel-heading"><div><Gamepad2 /><span><b>Game concept</b><small>Describe the experience</small></span></div></div>
          <label className="field"><span>Game title</span><input value={config.title} onChange={(event) => update('title', event.target.value)} maxLength={42} /><small className={validation.title ? '' : 'invalid'}>{config.title.length}/42 characters</small></label>
          <label className="field"><span>Generation prompt</span><textarea value={config.prompt} onChange={(event) => update('prompt', event.target.value)} rows={7} maxLength={400} /><small className={validation.prompt ? '' : 'invalid'}>{config.prompt.length}/400 characters · minimum 20</small></label>
          <div className="theme-options"><span>Visual theme</span><div>{['neon', 'solar', 'frost', 'mono'].map((theme) => <button type="button" key={theme} className={config.theme === theme ? `theme-swatch ${theme} active` : `theme-swatch ${theme}`} onClick={() => update('theme', theme)}><i />{theme}</button>)}</div></div>
          <div className="difficulty-control"><span>Difficulty</span><div>{(['easy', 'normal', 'hard'] as const).map((level) => <button type="button" className={config.difficulty === level ? 'active' : ''} onClick={() => update('difficulty', level)} key={level}>{level}</button>)}</div></div>
          {error && <p className="form-error">{error}</p>}
          <div className="generator-actions"><button className="button button-accent" type="submit" disabled={!valid || status === 'generating'}>{status === 'generating' ? <><LoaderCircle className="spin" /> Generating...</> : status === 'ready' ? <><Sparkles /> Regenerate</> : <><WandSparkles /> Generate game</>}</button><button type="button" className="button button-secondary" onClick={reset}><RotateCcw /> Reset</button>{status === 'ready' && <button type="button" className="button" onClick={play}><Gamepad2 /> Play now</button>}</div>
        </section>
        <aside className="generator-side">
          <div className="settings-panel"><div className="panel-heading"><div><SlidersHorizontal /><span><b>Game settings</b><small>Live configuration</small></span></div></div>
            <Range label="Player speed" value={config.playerSpeed} min={220} max={460} step={10} unit="px/s" onChange={(value) => update('playerSpeed', value)} />
            <Range label="Fire delay" value={config.fireRate} min={100} max={500} step={10} unit="ms" onChange={(value) => update('fireRate', value)} />
            <Range label="Enemy speed" value={config.enemySpeed} min={55} max={180} step={5} unit="px/s" onChange={(value) => update('enemySpeed', value)} />
            <Range label="Enemies / wave" value={config.enemyCount} min={4} max={16} step={1} unit="" onChange={(value) => update('enemyCount', value)} />
            <Range label="Starting lives" value={config.lives} min={1} max={5} step={1} unit="" onChange={(value) => update('lives', value)} />
            <Toggle label="Sound effects" value={config.sound} onChange={(value) => update('sound', value)} /><Toggle label="Screen shake" value={config.screenShake} onChange={(value) => update('screenShake', value)} />
          </div>
          <div className="config-preview"><div className="panel-heading"><div><Braces /><span><b>Config preview</b><small>Passed to Phaser</small></span></div></div><pre>{JSON.stringify(config, null, 2)}</pre></div>
        </aside>
      </form>
    </div>
  );
}

function Range({ label, value, min, max, step, unit, onChange }: { label: string; value: number; min: number; max: number; step: number; unit: string; onChange: (value: number) => void }) {
  return <label className="range-field"><span><b>{label}</b><em>{value}{unit}</em></span><input type="range" value={value} min={min} max={max} step={step} onChange={(event) => onChange(Number(event.target.value))} /></label>;
}
function Toggle({ label, value, onChange }: { label: string; value: boolean; onChange: (value: boolean) => void }) {
  return <label className="toggle-row"><span>{label}</span><input type="checkbox" checked={value} onChange={(event) => onChange(event.target.checked)} /><i /></label>;
}
