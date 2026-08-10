import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './AuthContext'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return <p role="status">Restoring your session…</p>
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}
