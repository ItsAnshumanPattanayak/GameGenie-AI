import type { AuthResponse, PreferenceInput, UserPreferences } from './types'

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
}
