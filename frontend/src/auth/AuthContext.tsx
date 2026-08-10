import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import type { PropsWithChildren } from 'react'

import { api } from '../api'
import type { AuthResponse, User } from '../types'

const REFRESH_KEY = 'gamegenie_refresh_token'

interface AuthContextValue {
  currentUser: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login(email: string, password: string): Promise<void>
  register(name: string, email: string, password: string): Promise<void>
  logout(): Promise<void>
  refreshSession(): Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: PropsWithChildren) {
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const refreshToken = useRef<string | null>(localStorage.getItem(REFRESH_KEY))
  const refreshInFlight = useRef<Promise<void> | null>(null)

  const applySession = useCallback((response: AuthResponse) => {
    setCurrentUser(response.user)
    setAccessToken(response.tokens.access_token)
    refreshToken.current = response.tokens.refresh_token
    localStorage.setItem(REFRESH_KEY, response.tokens.refresh_token)
  }, [])

  const clearSession = useCallback(() => {
    setCurrentUser(null)
    setAccessToken(null)
    refreshToken.current = null
    localStorage.removeItem(REFRESH_KEY)
  }, [])

  const refreshSession = useCallback(async () => {
    if (refreshInFlight.current) return refreshInFlight.current
    const operation = (async () => {
      if (!refreshToken.current) {
        clearSession()
        setIsLoading(false)
        return
      }
      try {
        applySession(await api.refresh(refreshToken.current))
      } catch {
        clearSession()
      } finally {
        setIsLoading(false)
      }
    })()
    refreshInFlight.current = operation
    try {
      await operation
    } finally {
      if (refreshInFlight.current === operation) refreshInFlight.current = null
    }
  }, [applySession, clearSession])

  useEffect(() => {
    void refreshSession()
  }, [refreshSession])

  const value = useMemo<AuthContextValue>(
    () => ({
      currentUser,
      accessToken,
      isAuthenticated: currentUser !== null && accessToken !== null,
      isLoading,
      login: async (email, password) => applySession(await api.login(email, password)),
      register: async (name, email, password) => applySession(await api.register(name, email, password)),
      logout: async () => {
        const token = refreshToken.current
        try {
          if (token) await api.logout(token)
        } finally {
          clearSession()
        }
      },
      refreshSession,
    }),
    [accessToken, applySession, clearSession, currentUser, isLoading, refreshSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used within AuthProvider')
  return value
}
