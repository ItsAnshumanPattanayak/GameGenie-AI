export type ScoreBreakdown = {
  genre: number;
  gameplay: number;
  mood: number;
  accessibility: number;
};

export type Game = {
  id: string;
  title: string;
  tagline: string;
  description: string;
  genre: string;
  platforms: string[];
  tags: string[];
  image: string;
  matchScore: number;
  breakdown: ScoreBreakdown;
  difficulty: 'Relaxed' | 'Balanced' | 'Challenging';
  playMode: 'Solo' | 'Co-op' | 'Multiplayer';
  releaseYear: number;
  featured?: boolean;
};

export type Preferences = {
  query: string;
  genres: string[];
  platforms: string[];
  moods: string[];
  difficulty: string;
  playMode: string;
};

export type GeneratorConfig = {
  title: string;
  prompt: string;
  theme: string;
  difficulty: 'easy' | 'normal' | 'hard';
  playerSpeed: number;
  fireRate: number;
  enemySpeed: number;
  enemyCount: number;
  lives: number;
  sound: boolean;
  screenShake: boolean;
};
