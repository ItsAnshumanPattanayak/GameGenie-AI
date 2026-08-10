export const TAXONOMY = {
  genres: [
    'action', 'adventure', 'role-playing', 'first-person shooter', 'third-person shooter',
    'strategy', 'simulation', 'puzzle', 'racing', 'sports', 'platformer', 'horror',
    'survival', 'battle royale', 'fighting', 'stealth', 'educational', 'rhythm',
    'sandbox', 'casual', 'exploration', 'music',
  ],
  platforms: ['PC', 'PlayStation', 'Xbox', 'Nintendo Switch', 'Android', 'iOS', 'macOS', 'Linux'],
  modes: ['single-player', 'multiplayer', 'cooperative', 'competitive', 'online', 'offline'],
  moods: ['relaxing', 'intense', 'dark', 'cheerful', 'atmospheric', 'scary', 'emotional', 'humorous', 'competitive', 'adventurous'],
  difficulty: ['easy', 'medium', 'hard'],
  price: ['free', 'paid'],
  hardware: ['low-end', 'mid-range', 'high-end'],
} as const
