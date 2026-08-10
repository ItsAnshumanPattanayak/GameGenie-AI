import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export function ProfilePage() {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  return (
    <section className="card page-card">
      <p className="eyebrow">Player profile</p>
      <h1>{currentUser?.name}</h1>
      <dl>
        <dt>Email</dt><dd>{currentUser?.email}</dd>
        <dt>Status</dt><dd>{currentUser?.is_active ? 'Active' : 'Inactive'}</dd>
        <dt>Member since</dt><dd>{currentUser ? new Date(currentUser.created_at).toLocaleDateString() : ''}</dd>
      </dl>
      <div className="actions">
        <Link className="button-link" to="/preferences">Edit preferences</Link>
        <button className="secondary" onClick={async () => { await logout(); navigate('/login') }}>Log out</button>
      </div>
    </section>
  )
}
