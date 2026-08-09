import GameCard from './GameCard';
import type { Game } from '../types';

export function GameGrid({ games }: { games: Game[] }) {
  return <div className="game-grid">{games.map((game) => <GameCard key={game.id} game={game} />)}</div>;
}

export function GameGridSkeleton({ count = 6 }: { count?: number }) {
  return <div className="game-grid" aria-label="Loading games">{Array.from({ length: count }, (_, index) => <div className="skeleton-card" key={index}><div /><i /><i /><span /></div>)}</div>;
}
