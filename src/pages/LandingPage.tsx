import { ArrowRight, BrainCircuit, Gamepad2, Search, SlidersHorizontal, Sparkles, WandSparkles } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { GameGrid } from '../components/GameGrid';
import { mockGames } from '../data/mockGames';

const ideas = ['Relaxing co-op adventure', 'Fast sci-fi arcade', 'Clever puzzle for short breaks'];

export default function LandingPage() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const submit = (event: FormEvent) => {
    event.preventDefault();
    navigate(`/discover${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ''}`);
  };

  return (
    <>
      <section className="hero">
        <div className="hero-art" aria-hidden="true">
          <img src="/covers/umbra.svg" alt="" /><img src="/covers/nova.svg" alt="" /><img src="/covers/moss.svg" alt="" />
        </div>
        <div className="page-width hero-content">
          <span className="eyebrow"><Sparkles size={15} /> AI-assisted game discovery</span>
          <h1>Find the game that fits <span>right now.</span></h1>
          <p>Describe what you feel like playing. GameGenie turns the details into a ranked, explainable set of matches.</p>
          <form className="prompt-bar" onSubmit={submit}>
            <Search size={21} aria-hidden="true" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try: a relaxing mystery I can finish this weekend" aria-label="Describe the game you want" />
            <button className="button" type="submit">Find games <ArrowRight size={18} /></button>
          </form>
          <div className="quick-prompts" aria-label="Search suggestions">
            {ideas.map((idea) => <button key={idea} onClick={() => { setQuery(idea); navigate(`/discover?q=${encodeURIComponent(idea)}`); }}>{idea}</button>)}
          </div>
          <div className="trust-row">
            <span><b>12</b> curated games</span><i /><span><b>4-part</b> match scoring</span><i /><span><b>1</b> playable generator</span>
          </div>
        </div>
      </section>

      <section className="section page-width">
        <div className="section-heading">
          <div><span className="eyebrow">Picked for curious players</span><h2>High-match discoveries</h2></div>
          <Link to="/discover" className="text-link">Browse all <ArrowRight size={17} /></Link>
        </div>
        <GameGrid games={mockGames.slice(0, 6)} />
      </section>

      <section className="process-band">
        <div className="page-width">
          <div className="section-heading"><div><span className="eyebrow">From thought to play</span><h2>One idea, three useful steps</h2></div></div>
          <div className="process-grid">
            <div><span><BrainCircuit /></span><b>01</b><h3>Describe your mood</h3><p>Write naturally. Genre, pace, platform, and company are all useful signals.</p></div>
            <div><span><SlidersHorizontal /></span><b>02</b><h3>Shape the shortlist</h3><p>Refine the results and inspect exactly why each match earned its score.</p></div>
            <div><span><Gamepad2 /></span><b>03</b><h3>Make it playable</h3><p>Configure a Space Shooter from your prompt and jump directly into the game.</p></div>
          </div>
        </div>
      </section>

      <section className="creator-band page-width">
        <div><span className="eyebrow"><WandSparkles size={15} /> Game generator</span><h2>Can’t find it? Shape it.</h2><p>Set the theme, challenge, player speed, enemy pressure, and effects. Then play the result immediately.</p></div>
        <Link to="/generator" className="button button-accent">Open generator <ArrowRight size={18} /></Link>
      </section>
    </>
  );
}
