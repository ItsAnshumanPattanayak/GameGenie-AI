import { lazy, Suspense } from 'react'
import { Link, Navigate, Outlet, Route, Routes } from 'react-router-dom'

import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
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
  return <Suspense fallback={<p role="status">Loading game studio…</p>}><GameStudioPage /></Suspense>
}

function SavedGameRoute() {
  return <Suspense fallback={<p role="status">Loading saved game…</p>}><SavedGamePlayerPage /></Suspense>
}

function PublicGameRoute() {
  return <Suspense fallback={<p role="status">Loading shared game…</p>}><PublicSharedGamePage /></Suspense>
}

function AccountLayout() {
  return <><header><Link className="brand" to="/dashboard">GameGenie <span>AI</span></Link><nav><Link to="/dashboard">Dashboard</Link><Link to="/my-games">My Games</Link><Link to="/generator">Generate</Link><Link to="/history">History</Link><Link to="/favourites">Favourites</Link><Link to="/preferences">Preferences</Link><Link to="/profile">Profile</Link></nav></header><main className="app-shell"><Outlet /></main></>
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
