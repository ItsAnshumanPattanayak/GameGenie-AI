import { ArrowLeft, ArrowRight, Check, Gamepad2, Monitor, Sparkles, Users } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { GameGrid } from '../components/GameGrid';
import { mockGames } from '../data/mockGames';

export default function GameDetailPage() {
  const { gameId } = useParams();
  const game = mockGames.find((item) => item.id === gameId);
  if (!game) return <div className="page-width page-top empty-state"><Gamepad2 /><h1>Game not found</h1><p>That game may have moved out of this collection.</p><Link className="button" to="/discover">Back to discovery</Link></div>;
  const related = mockGames.filter((item) => item.id !== game.id && (item.genre === game.genre || item.playMode === game.playMode)).slice(0, 3);
  return (
    <div className="detail-page">
      <div className="detail-hero">
        <img src={game.image} alt="" aria-hidden="true" className="detail-backdrop" />
        <div className="detail-overlay" />
        <div className="page-width detail-content">
          <Link to="/discover" className="back-link"><ArrowLeft size={17} /> Back to discovery</Link>
          <div className="detail-grid">
            <img className="detail-cover" src={game.image} alt={`${game.title} cover art`} />
            <div><span className="eyebrow"><Sparkles size={15} /> {game.matchScore}% match</span><h1>{game.title}</h1><p className="detail-tagline">{game.tagline}</p><p>{game.description}</p>
              <div className="detail-meta"><span><Gamepad2 /> {game.genre}</span><span><Users /> {game.playMode}</span><span><Monitor /> {game.platforms.join(' / ')}</span></div>
              <div className="tag-list">{game.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
              <div className="detail-actions">{game.id === 'nova-drift' ? <Link to="/play/space-shooter" className="button button-accent">Play now <ArrowRight size={18} /></Link> : <Link to={`/generator?inspiredBy=${game.id}`} className="button button-accent">Create something similar <Sparkles size={17} /></Link>}<Link to="/generator" className="button button-secondary">Open generator</Link></div>
            </div>
          </div>
        </div>
      </div>
      <section className="page-width section detail-lower">
        <div className="why-match"><div><span className="eyebrow">Match explanation</span><h2>Why GameGenie chose this</h2><p>The score combines your selected genre, desired gameplay, mood, and accessibility signals.</p></div><div className="detail-score-grid">{Object.entries(game.breakdown).map(([label, score]) => <div key={label}><span><Check /></span><h3>{label}</h3><b>{score}%</b><i><u style={{ width: `${score}%` }} /></i></div>)}</div></div>
        {related.length > 0 && <div className="related"><div className="section-heading"><div><span className="eyebrow">Keep exploring</span><h2>Related matches</h2></div></div><GameGrid games={related} /></div>}
      </section>
    </div>
  );
}
