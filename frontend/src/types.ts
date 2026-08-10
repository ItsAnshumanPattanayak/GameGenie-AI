export interface User {
  id: string
  name: string
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface AuthResponse {
  success: true
  user: User
  tokens: AuthTokens
}

export interface UserPreferences {
  user_id: string
  preferred_genres: string[]
  preferred_platforms: string[]
  preferred_modes: string[]
  preferred_moods: string[]
  preferred_difficulty: string | null
  price_preference: string | null
  hardware_level: string | null
  updated_at: string
}

export type PreferenceInput = Omit<UserPreferences, 'user_id' | 'updated_at'>
