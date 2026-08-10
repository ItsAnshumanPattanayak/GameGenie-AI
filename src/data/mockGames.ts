import type { Game } from '../types';

export const mockGames: Game[] = [
  {
    id: 'nova-drift', title: 'Nova Drift', tagline: 'Outfly the collapsing frontier',
    description: 'A responsive arcade space shooter with evolving enemy formations, fast upgrades, and crisp score chasing.',
    genre: 'Arcade', platforms: ['Web', 'PC'], tags: ['Space', 'Fast-paced', 'Score attack'], image: '/covers/nova.svg',
    matchScore: 96, breakdown: { genre: 98, gameplay: 97, mood: 93, accessibility: 94 }, difficulty: 'Balanced', playMode: 'Solo', releaseYear: 2026, featured: true,
  },
  {
    id: 'echoes-of-umbra', title: 'Echoes of Umbra', tagline: 'Every shadow remembers',
    description: 'Explore a living mystery world where clues change shape and every conversation alters the final chapter.',
    genre: 'Adventure', platforms: ['PC', 'Console'], tags: ['Story-rich', 'Mystery', 'Choices'], image: '/covers/umbra.svg',
    matchScore: 93, breakdown: { genre: 95, gameplay: 88, mood: 98, accessibility: 91 }, difficulty: 'Relaxed', playMode: 'Solo', releaseYear: 2025, featured: true,
  },
  {
    id: 'circuit-crown', title: 'Circuit Crown', tagline: 'Build fast. Rule the grid.',
    description: 'A tactical arena builder where compact machines clash in readable, five-minute competitive rounds.',
    genre: 'Strategy', platforms: ['Web', 'Mobile'], tags: ['Tactics', 'Builder', 'Competitive'], image: '/covers/circuit.svg',
    matchScore: 91, breakdown: { genre: 96, gameplay: 94, mood: 85, accessibility: 87 }, difficulty: 'Challenging', playMode: 'Multiplayer', releaseYear: 2026,
  },
  {
    id: 'moss-and-moonlight', title: 'Moss & Moonlight', tagline: 'A quieter kind of quest',
    description: 'Restore a moonlit garden, befriend curious spirits, and discover gentle stories at your own pace.',
    genre: 'Cozy', platforms: ['PC', 'Console'], tags: ['Relaxing', 'Decorating', 'Nature'], image: '/covers/moss.svg',
    matchScore: 90, breakdown: { genre: 92, gameplay: 84, mood: 99, accessibility: 95 }, difficulty: 'Relaxed', playMode: 'Solo', releaseYear: 2025,
  },
  {
    id: 'velocity-zero', title: 'Velocity Zero', tagline: 'Speed has consequences',
    description: 'Thread anti-gravity tracks through a vivid orbital city while rewinding your boldest mistakes.',
    genre: 'Racing', platforms: ['PC', 'Console'], tags: ['Sci-fi', 'Time trial', 'High speed'], image: '/covers/velocity.svg',
    matchScore: 88, breakdown: { genre: 91, gameplay: 95, mood: 86, accessibility: 80 }, difficulty: 'Challenging', playMode: 'Multiplayer', releaseYear: 2024,
  },
  {
    id: 'paper-dungeons', title: 'Paper Dungeons', tagline: 'Fold the world to find the way',
    description: 'A tactile puzzle adventure where rooms fold, rotate, and connect like an impossible pop-up book.',
    genre: 'Puzzle', platforms: ['Web', 'Mobile'], tags: ['Clever', 'Short sessions', 'Handcrafted'], image: '/covers/paper.svg',
    matchScore: 87, breakdown: { genre: 94, gameplay: 91, mood: 83, accessibility: 82 }, difficulty: 'Balanced', playMode: 'Solo', releaseYear: 2026,
  },
  {
    id: 'hearthbound', title: 'Hearthbound', tagline: 'Carry the flame together',
    description: 'Two travelers cross a frozen world, combining tools and timing to keep a shared ember alive.',
    genre: 'Adventure', platforms: ['PC', 'Console'], tags: ['Co-op', 'Emotional', 'Exploration'], image: '/covers/umbra.svg',
    matchScore: 86, breakdown: { genre: 89, gameplay: 90, mood: 92, accessibility: 75 }, difficulty: 'Balanced', playMode: 'Co-op', releaseYear: 2025,
  },
  {
    id: 'tiny-titans', title: 'Tiny Titans', tagline: 'Pocket heroes, enormous plans',
    description: 'Draft a miniature squad and outthink rivals in playful turn-based battles built for quick sessions.',
    genre: 'Strategy', platforms: ['Web', 'Mobile'], tags: ['Turn-based', 'Team builder', 'Quick play'], image: '/covers/circuit.svg',
    matchScore: 84, breakdown: { genre: 90, gameplay: 87, mood: 82, accessibility: 78 }, difficulty: 'Balanced', playMode: 'Multiplayer', releaseYear: 2024,
  },
  {
    id: 'afterglow', title: 'Afterglow', tagline: 'The city wakes after midnight',
    description: 'Skate through a rhythmic neon city, chaining movement and music into one uninterrupted flow.',
    genre: 'Rhythm', platforms: ['PC', 'Console'], tags: ['Music', 'Movement', 'Stylish'], image: '/covers/velocity.svg',
    matchScore: 82, breakdown: { genre: 88, gameplay: 85, mood: 90, accessibility: 66 }, difficulty: 'Challenging', playMode: 'Solo', releaseYear: 2025,
  },
  {
    id: 'bloomcraft', title: 'Bloomcraft', tagline: 'Grow a world worth sharing',
    description: 'Build floating gardens with friends and trade seeds, structures, and stories across connected islands.',
    genre: 'Cozy', platforms: ['PC', 'Mobile'], tags: ['Creative', 'Farming', 'Social'], image: '/covers/moss.svg',
    matchScore: 81, breakdown: { genre: 86, gameplay: 76, mood: 94, accessibility: 70 }, difficulty: 'Relaxed', playMode: 'Co-op', releaseYear: 2026,
  },
  {
    id: 'the-last-signal', title: 'The Last Signal', tagline: 'Answer carefully',
    description: 'Decode transmissions from an abandoned research station while something learns how you respond.',
    genre: 'Horror', platforms: ['PC'], tags: ['Atmospheric', 'Mystery', 'Psychological'], image: '/covers/umbra.svg',
    matchScore: 79, breakdown: { genre: 85, gameplay: 72, mood: 96, accessibility: 63 }, difficulty: 'Balanced', playMode: 'Solo', releaseYear: 2024,
  },
  {
    id: 'skyline-strikers', title: 'Skyline Strikers', tagline: 'Own every rooftop',
    description: 'A bright team arena where momentum, passing, and environmental tricks reward clever coordination.',
    genre: 'Sports', platforms: ['PC', 'Console'], tags: ['Team play', 'Arcade', 'Competitive'], image: '/covers/nova.svg',
    matchScore: 77, breakdown: { genre: 80, gameplay: 88, mood: 73, accessibility: 67 }, difficulty: 'Challenging', playMode: 'Multiplayer', releaseYear: 2025,
  },
];

export const allGenres = [...new Set(mockGames.map((game) => game.genre))].sort();
export const allPlatforms = [...new Set(mockGames.flatMap((game) => game.platforms))].sort();
