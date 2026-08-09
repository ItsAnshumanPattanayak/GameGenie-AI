import { apiBaseUrl, apiClient } from './apiClient';
import { mockGames } from '../data/mockGames';
import type { Game, GeneratorConfig, Preferences } from '../types';

const localInterpret = (query: string): Partial<Preferences> => {
  const input = query.toLowerCase();
  const genres = ['arcade', 'adventure', 'strategy', 'cozy', 'racing', 'puzzle', 'rhythm', 'horror', 'sports']
    .filter((genre) => input.includes(genre))
    .map((genre) => genre[0].toUpperCase() + genre.slice(1));
  return {
    query,
    genres,
    moods: ['relaxing', 'competitive', 'story-rich', 'fast-paced'].filter((mood) => input.includes(mood)),
    playMode: input.includes('co-op') || input.includes('with friends') ? 'Co-op' : '',
  };
};

export async function interpretSearch(query: string): Promise<Partial<Preferences>> {
  if (!apiBaseUrl) return localInterpret(query);
  try {
    const { data } = await apiClient.post('/api/search/interpret', { query });
    return data.preferences ?? data;
  } catch {
    return localInterpret(query);
  }
}

export async function recommendGames(preferences: Preferences): Promise<Game[]> {
  if (apiBaseUrl) {
    try {
      const { data } = await apiClient.post('/api/search/recommend', preferences);
      return data.games ?? data.recommendations ?? data;
    } catch {
      // The product remains useful during local development and backend outages.
    }
  }

  const terms = `${preferences.query} ${preferences.moods.join(' ')}`.toLowerCase().split(/\s+/).filter(Boolean);
  return mockGames
    .map((game) => {
      let boost = 0;
      if (preferences.genres.includes(game.genre)) boost += 12;
      if (preferences.platforms.some((platform) => game.platforms.includes(platform))) boost += 7;
      if (preferences.difficulty === game.difficulty) boost += 5;
      if (preferences.playMode === game.playMode) boost += 5;
      const haystack = `${game.title} ${game.genre} ${game.tags.join(' ')} ${game.description}`.toLowerCase();
      boost += terms.filter((term) => term.length > 2 && haystack.includes(term)).length * 3;
      return { ...game, matchScore: Math.min(99, game.matchScore + boost) };
    })
    .sort((a, b) => b.matchScore - a.matchScore);
}

export async function generateGame(config: GeneratorConfig): Promise<GeneratorConfig> {
  if (apiBaseUrl) {
    try {
      const { data } = await apiClient.post('/api/generator/generate', config);
      return data.config ?? data;
    } catch {
      // Fall through to the deterministic local generator.
    }
  }
  await new Promise((resolve) => window.setTimeout(resolve, 650));
  return config;
}
