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

export interface Game {
  id: string
  title: string
  description?: string | null
  short_description?: string | null
  genres: string[]
  platforms: string[]
  developer?: string | null
  release_year?: number | null
  rating?: number | null
  price?: string | number | null
  price_category: string
  image_url?: string | null
}

export interface SearchHistory {
  id: string
  query: string
  extracted_preferences: Record<string, unknown>
  result_count: number
  processing_time_ms: number
  created_at: string
}

export interface FavouriteGame {
  id: string
  game_id: string
  created_at: string
  game: Game
}

export type FeedbackType = 'relevant' | 'not_relevant' | 'interested' | 'already_played'

export interface RecommendationItem {
  game: Game
  score: number
  explanation: string
  matched_attributes: string[]
}

export interface RecommendationResponse {
  success: true
  items: RecommendationItem[]
  search_id: string | null
}
