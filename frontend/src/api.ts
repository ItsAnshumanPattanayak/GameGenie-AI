import type {
  AuthResponse,
  FavouriteGame,
  FeedbackType,
  PreferenceInput,
  RecommendationResponse,
  SearchHistory,
  UserPreferences,
} from './types'
import type { GeneratorResponse } from './games/types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

interface ErrorBody {
  error?: { code?: string; message?: string }
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code = 'API_ERROR',
  ) {
    super(message)
  }
}

async function request<T>(path: string, init: RequestInit = {}, accessToken?: string): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  const response = await fetch(`${API_URL}${path}`, { ...init, headers })
  const body = (await response.json().catch(() => ({}))) as T & ErrorBody
  if (!response.ok) {
    throw new ApiError(body.error?.message ?? 'The request failed.', response.status, body.error?.code)
  }
  return body
}

export const api = {
  register: (name: string, email: string, password: string) =>
    request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }),
  login: (email: string, password: string) =>
    request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  refresh: (refreshToken: string) =>
    request<AuthResponse>('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),
  logout: (refreshToken: string) =>
    request<{ success: true }>('/api/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),
  preferences: (accessToken: string) =>
    request<{ success: true; preferences: UserPreferences }>('/api/preferences', {}, accessToken),
  updatePreferences: (accessToken: string, preferences: PreferenceInput) =>
    request<{ success: true; preferences: UserPreferences }>(
      '/api/preferences',
      { method: 'PUT', body: JSON.stringify(preferences) },
      accessToken,
    ),
  searchHistory: (accessToken: string) =>
    request<{ success: true; items: SearchHistory[] }>('/api/history/searches', {}, accessToken),
  searchHistoryItem: (accessToken: string, searchId: string) =>
    request<{ success: true; item: SearchHistory }>(`/api/history/searches/${searchId}`, {}, accessToken),
  deleteSearchHistory: (accessToken: string, searchId: string) =>
    request<{ success: true; deleted_count: number }>(
      `/api/history/searches/${searchId}`,
      { method: 'DELETE' },
      accessToken,
    ),
  deleteAllSearchHistory: (accessToken: string) =>
    request<{ success: true; deleted_count: number }>('/api/history/searches', { method: 'DELETE' }, accessToken),
  favourites: (accessToken: string) =>
    request<{ success: true; items: FavouriteGame[] }>('/api/favourites', {}, accessToken),
  addFavourite: (accessToken: string, gameId: string) =>
    request<{ success: true; created: boolean; item: FavouriteGame }>(
      `/api/favourites/${gameId}`,
      { method: 'POST' },
      accessToken,
    ),
  removeFavourite: (accessToken: string, gameId: string) =>
    request<{ success: true; deleted_count: number }>(
      `/api/favourites/${gameId}`,
      { method: 'DELETE' },
      accessToken,
    ),
  submitFeedback: (accessToken: string, gameId: string, feedbackType: FeedbackType, searchId?: string | null) =>
    request<{ success: true; item: { id: string; feedback_type: FeedbackType } }>(
      '/api/feedback',
      { method: 'POST', body: JSON.stringify({ game_id: gameId, feedback_type: feedbackType, search_id: searchId }) },
      accessToken,
    ),
  feedback: (accessToken: string) =>
    request<{ success: true; items: Array<{ id: string; game_id: string; feedback_type: FeedbackType }> }>(
      '/api/feedback',
      {},
      accessToken,
    ),
  recommend: (prompt: string, accessToken?: string) =>
    request<RecommendationResponse>(
      '/api/search/recommend',
      { method: 'POST', body: JSON.stringify({ prompt, limit: 10 }) },
      accessToken,
    ),
  generateGame: (prompt: string, selectedGameId?: string | null) =>
    request<GeneratorResponse>('/api/generator/interpret', {
      method: 'POST',
      body: JSON.stringify({ prompt, selected_game_id: selectedGameId ?? null, overrides: {} }),
    }),
}
