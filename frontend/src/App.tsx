import { Link, Navigate, Outlet, Route, Routes } from 'react-router-dom'

import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { PreferencesPage } from './pages/PreferencesPage'
import { ProfilePage } from './pages/ProfilePage'
import { RegisterPage } from './pages/RegisterPage'

function AccountLayout() {
  return <><header><Link className="brand" to="/dashboard">GameGenie <span>AI</span></Link><nav><Link to="/dashboard">Dashboard</Link><Link to="/preferences">Preferences</Link><Link to="/profile">Profile</Link></nav></header><main className="app-shell"><Outlet /></main></>
}

export function App() {
  return <AuthProvider><Routes>
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route element={<ProtectedRoute />}><Route element={<AccountLayout />}>
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route path="/preferences" element={<PreferencesPage />} />
      <Route path="/history" element={<PlaceholderPage title="History" />} />
      <Route path="/favourites" element={<PlaceholderPage title="Favourites" />} />
      <Route path="/my-games" element={<PlaceholderPage title="My games" />} />
    </Route></Route>
    <Route path="*" element={<Navigate to="/dashboard" replace />} />
  </Routes></AuthProvider>
}
