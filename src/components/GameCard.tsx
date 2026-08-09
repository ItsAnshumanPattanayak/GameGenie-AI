import { ArrowRight, Info, RotateCcw, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { Game } from '../types';

export default function GameCard({ game }: { game: Game }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <article className={flipped ? 'game-card flipped' : 'game-card'}>
      <div className="game-card-inner">
        <div className="game-card-face game-card-front">
          <div className="cover-wrap">
            <img src={game.image} alt={`${game.title} cover art`} loading="lazy" />
            <span className="genre-pill">{game.genre}</span>
            <div className="score-ring" style={{ '--score': `${game.matchScore * 3.6}deg` } as React.CSSProperties}>
              <span>{game.matchScore}</span><small>match</small>
            </div>
          </div>
          <div className="card-body">
            <div><h3>{game.title}</h3><p className="tagline">{game.tagline}</p></div>
            <div className="tag-list">{game.tags.slice(0, 3).map((tag) => <span key={tag}>{tag}</span>)}</div>
            <div className="card-actions">
              <Link to={`/games/${game.id}`} className="button button-small">Details <ArrowRight size={15} /></Link>
              <button className="icon-btn" onClick={() => setFlipped(true)} title="Show match breakdown" aria-label={`Show ${game.title} match breakdown`}><Info size={18} /></button>
            </div>
          </div>
        </div>
        <div className="game-card-face game-card-back">
          <div className="card-back-head"><div><span className="eyebrow">Why it fits</span><h3>{game.title}</h3></div><Sparkles size={21} /></div>
          <p>{game.description}</p>
          <div className="score-bars">
            {Object.entries(game.breakdown).map(([label, score]) => (
              <div key={label}><span><b>{label}</b><em>{score}%</em></span><i><u style={{ width: `${score}%` }} /></i></div>
            ))}
          </div>
          <div className="card-actions">
            <Link to={`/games/${game.id}`} className="button button-small">View game <ArrowRight size={15} /></Link>
            <button className="icon-btn" onClick={() => setFlipped(false)} title="Show cover" aria-label={`Show ${game.title} cover`}><RotateCcw size={18} /></button>
          </div>
        </div>
      </div>
    </article>
  );
}
