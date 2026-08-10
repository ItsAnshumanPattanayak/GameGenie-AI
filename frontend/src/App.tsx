import { lazy, Suspense } from 'react'
import { Link, Navigate, NavLink, Outlet, Route, Routes } from 'react-router-dom'

import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { LoadingState } from './components/PageState'
import { DashboardPage } from './pages/DashboardPage'
import { FavouritesPage } from './pages/FavouritesPage'
import { HistoryPage } from './pages/HistoryPage'
import { LoginPage } from './pages/LoginPage'
import { MyGamesPage } from './pages/MyGamesPage'
import { PreferencesPage } from './pages/PreferencesPage'
import { ProfilePage } from './pages/ProfilePage'
import { RegisterPage } from './pages/RegisterPage'

const GameStudioPage = lazy(async () => ({ default: (await import('./pages/GameStudioPage')).GameStudioPage }))
const SavedGamePlayerPage = lazy(async () => ({ default: (await import('./pages/SavedGamePlayerPage')).SavedGamePlayerPage }))
const PublicSharedGamePage = lazy(async () => ({ default: (await import('./pages/PublicSharedGamePage')).PublicSharedGamePage }))

function GameStudioRoute() {
  return <Suspense fallback={<LoadingState message="Loading game studio…" />}><GameStudioPage /></Suspense>
}

function SavedGameRoute() {
  return <Suspense fallback={<LoadingState message="Loading saved game…" />}><SavedGamePlayerPage /></Suspense>
}

function PublicGameRoute() {
  return <Suspense fallback={<LoadingState message="Loading shared game…" fullPage />}><PublicSharedGamePage /></Suspense>
}

const navigation = [
  ['/dashboard', 'Dashboard'], ['/my-games', 'My Games'], ['/generator', 'Generate'],
  ['/history', 'History'], ['/favourites', 'Favourites'], ['/preferences', 'Preferences'], ['/profile', 'Profile'],
] as const

function AccountLayout() {
  return <><a className="skip-link" href="#main-content">Skip to main content</a><header className="site-header"><Link className="brand" to="/dashboard">GameGenie <span>AI</span></Link><nav aria-label="Primary navigation">{navigation.map(([to, label]) => <NavLink key={to} to={to} className={({ isActive }) => isActive ? 'active' : undefined}>{label}</NavLink>)}</nav></header><main id="main-content" className="app-shell"><Outlet /></main></>
}

export function App() {
  return <AuthProvider><Routes>
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/shared/:slug" element={<PublicGameRoute />} />
    <Route element={<ProtectedRoute />}><Route element={<AccountLayout />}>
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route path="/preferences" element={<PreferencesPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/favourites" element={<FavouritesPage />} />
      <Route path="/my-games" element={<MyGamesPage />} />
      <Route path="/generator" element={<GameStudioRoute />} />
      <Route path="/play/saved/:id" element={<SavedGameRoute />} />
    </Route></Route>
    <Route path="*" element={<Navigate to="/dashboard" replace />} />
  </Routes></AuthProvider>
}
