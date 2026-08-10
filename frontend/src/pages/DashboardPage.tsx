import { Link } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export function DashboardPage() {
  const { currentUser } = useAuth()
  return <section className="card page-card"><p className="eyebrow">Dashboard</p><h1>Welcome, {currentUser?.name}</h1><p>Your account foundation is ready. Set your controlled preferences now; personalised ranking will arrive in a later phase.</p><Link className="button-link" to="/preferences">Set preferences</Link></section>
}
