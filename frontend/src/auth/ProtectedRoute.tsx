import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { LoadingState } from '../components/PageState'
import { useAuth } from './AuthContext'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return <LoadingState message="Restoring your session…" fullPage />
  if (!isAuthenticated) {
    const from = `${location.pathname}${location.search}${location.hash}`
    return <Navigate to="/login" replace state={{ from }} />
  }
  return <Outlet />
}
