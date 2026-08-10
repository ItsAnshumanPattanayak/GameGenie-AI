import type { AuthResponse, UserPreferences } from '../types'

export const authResponse: AuthResponse = {
  success: true,
  user: {
    id: 'user-1', name: 'Player One', email: 'player@example.com', is_active: true,
    created_at: '2026-08-10T00:00:00Z', updated_at: '2026-08-10T00:00:00Z',
  },
  tokens: { access_token: 'access-token', refresh_token: 'refresh-token', token_type: 'bearer', expires_in: 900 },
}

export const preferences: UserPreferences = {
  user_id: 'user-1', preferred_genres: [], preferred_platforms: [], preferred_modes: [], preferred_moods: [],
  preferred_difficulty: null, price_preference: null, hardware_level: null, updated_at: '2026-08-10T00:00:00Z',
}

export function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}
