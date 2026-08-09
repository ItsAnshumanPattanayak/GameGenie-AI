import { AlertCircle, ChevronDown, Filter, Search, SlidersHorizontal, X } from 'lucide-react';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { GameGrid, GameGridSkeleton } from '../components/GameGrid';
import { allGenres, allPlatforms, mockGames } from '../data/mockGames';
import { interpretSearch, recommendGames } from '../api/gameApi';
import type { Game, Preferences } from '../types';

const defaultPreferences: Preferences = { query: '', genres: [], platforms: [], moods: [], difficulty: '', playMode: '' };
const moods = ['Relaxing', 'Story-rich', 'Fast-paced', 'Competitive'];

export default function DiscoverPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') ?? '';
  const [preferences, setPreferences] = useState<Preferences>({ ...defaultPreferences, query: initialQuery });
  const [games, setGames] = useState<Game[]>(mockGames);
  const [sort, setSort] = useState('match');
  const [loading, setLoading] = useState(Boolean(initialQuery));
  const [error, setError] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(false);

  const runSearch = async (next: Preferences) => {
    setLoading(true); setError('');
    try {
      const interpreted = next.query ? await interpretSearch(next.query) : {};
      const merged = { ...next, ...interpreted, genres: next.genres.length ? next.genres : interpreted.genres ?? [] };
      setPreferences(merged);
      setGames(await recommendGames(merged));
      setSearchParams(merged.query ? { q: merged.query } : {});
    } catch {
      setError('We could not refresh your matches. Try again in a moment.');
    } finally { setLoading(false); }
  };

  useEffect(() => { if (initialQuery) void runSearch({ ...defaultPreferences, query: initialQuery }); }, []);

  const visibleGames = useMemo(() => {
    const filtered = games.filter((game) =>
      (!preferences.genres.length || preferences.genres.includes(game.genre)) &&
      (!preferences.platforms.length || preferences.platforms.some((item) => game.platforms.includes(item))) &&
      (!preferences.difficulty || preferences.difficulty === game.difficulty) &&
      (!preferences.playMode || preferences.playMode === game.playMode));
    return [...filtered].sort((a, b) => sort === 'newest' ? b.releaseYear - a.releaseYear : sort === 'title' ? a.title.localeCompare(b.title) : b.matchScore - a.matchScore);
  }, [games, preferences, sort]);

  const toggleArray = (key: 'genres' | 'platforms' | 'moods', value: string) => {
    setPreferences((current) => ({ ...current, [key]: current[key].includes(value) ? current[key].filter((item) => item !== value) : [...current[key], value] }));
  };
  const submit = (event: FormEvent) => { event.preventDefault(); void runSearch(preferences); };
  const clear = () => { setPreferences(defaultPreferences); setGames(mockGames); setSearchParams({}); };
  const activeCount = preferences.genres.length + preferences.platforms.length + preferences.moods.length + Number(Boolean(preferences.difficulty)) + Number(Boolean(preferences.playMode));

  return (
    <div className="page-width page-top discover-page">
      <div className="page-title-row"><div><span className="eyebrow">Recommendation studio</span><h1>Discover your next favorite</h1><p>Search naturally, then tune the signals that matter.</p></div></div>
      <form className="discovery-search" onSubmit={submit}>
        <Search size={20} /><input value={preferences.query} onChange={(event) => setPreferences({ ...preferences, query: event.target.value })} placeholder="Describe what you want to play..." aria-label="Search games" />
        {preferences.query && <button type="button" className="icon-btn" onClick={() => setPreferences({ ...preferences, query: '' })} aria-label="Clear search"><X size={18} /></button>}
        <button className="button" type="submit">Update matches</button>
      </form>
      <div className="preference-strip"><span><SlidersHorizontal size={17} /> Mood</span>{moods.map((mood) => <button className={preferences.moods.includes(mood) ? 'chip active' : 'chip'} key={mood} onClick={() => toggleArray('moods', mood)}>{mood}</button>)}</div>
      <button className="button filter-toggle" onClick={() => setFiltersOpen(true)}><Filter size={17} /> Filters {activeCount > 0 && <b>{activeCount}</b>}</button>

      <div className="discover-layout">
        <aside className={filtersOpen ? 'filters open' : 'filters'}>
          <div className="filters-head"><div><Filter size={18} /><h2>Filters</h2>{activeCount > 0 && <span>{activeCount}</span>}</div><button className="icon-btn mobile-only" onClick={() => setFiltersOpen(false)} aria-label="Close filters"><X /></button></div>
          <FilterGroup label="Genre" values={allGenres} selected={preferences.genres} onToggle={(value) => toggleArray('genres', value)} />
          <FilterGroup label="Platform" values={allPlatforms} selected={preferences.platforms} onToggle={(value) => toggleArray('platforms', value)} />
          <SelectFilter label="Difficulty" value={preferences.difficulty} options={['Relaxed', 'Balanced', 'Challenging']} onChange={(value) => setPreferences({ ...preferences, difficulty: value })} />
          <SelectFilter label="Play mode" value={preferences.playMode} options={['Solo', 'Co-op', 'Multiplayer']} onChange={(value) => setPreferences({ ...preferences, playMode: value })} />
          <button className="text-button" onClick={clear}>Clear all filters</button>
          <button className="button mobile-only" onClick={() => setFiltersOpen(false)}>Show {visibleGames.length} games</button>
        </aside>
        {filtersOpen && <button className="filter-scrim" onClick={() => setFiltersOpen(false)} aria-label="Close filters" />}

        <section className="results" aria-live="polite">
          <div className="results-head"><div><h2>{loading ? 'Finding matches...' : `${visibleGames.length} matches`}</h2><p>Scores adapt to your preferences.</p></div><label className="sort-select">Sort <span><select value={sort} onChange={(event) => setSort(event.target.value)}><option value="match">Best match</option><option value="newest">Newest</option><option value="title">Title</option></select><ChevronDown size={16} /></span></label></div>
          {error && <div className="error-banner"><AlertCircle /><span>{error}</span><button onClick={() => void runSearch(preferences)}>Retry</button></div>}
          {loading ? <GameGridSkeleton /> : visibleGames.length ? <GameGrid games={visibleGames} /> : <div className="empty-state"><Search /><h2>No exact matches</h2><p>Remove a filter or try a broader description.</p><button className="button" onClick={clear}>Reset filters</button></div>}
        </section>
      </div>
    </div>
  );
}

function FilterGroup({ label, values, selected, onToggle }: { label: string; values: string[]; selected: string[]; onToggle: (value: string) => void }) {
  return <fieldset><legend>{label}</legend>{values.map((value) => <label className="check-row" key={value}><input type="checkbox" checked={selected.includes(value)} onChange={() => onToggle(value)} /><span>{value}</span></label>)}</fieldset>;
}

function SelectFilter({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return <label className="filter-select"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}><option value="">Any</option>{options.map((option) => <option key={option}>{option}</option>)}</select></label>;
}
