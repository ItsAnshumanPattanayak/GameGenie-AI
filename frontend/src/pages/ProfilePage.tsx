import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { errorMessage } from '../api'
import { useAuth } from '../auth/AuthContext'
import { ErrorState } from '../components/PageState'

export function ProfilePage() {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const [loggingOut, setLoggingOut] = useState(false)
  const [error, setError] = useState('')

  async function signOut() {
    setLoggingOut(true); setError('')
    try {
      await logout()
      navigate('/login', { replace: true })
    } catch (reason) {
      setError(errorMessage(reason, 'Could not log out. Please try again.'))
      setLoggingOut(false)
    }
  }
  return (
    <section className="card page-card">
      <p className="eyebrow">Player profile</p>
      <h1>{currentUser?.name}</h1>
      <dl>
        <dt>Email</dt><dd>{currentUser?.email}</dd>
        <dt>Status</dt><dd>{currentUser?.is_active ? 'Active' : 'Inactive'}</dd>
        <dt>Member since</dt><dd>{currentUser ? new Date(currentUser.created_at).toLocaleDateString() : ''}</dd>
      </dl>
      {error && <ErrorState message={error} />}
      <div className="actions">
        <Link className="button-link" to="/preferences">Edit preferences</Link>
        <button className="secondary" disabled={loggingOut} onClick={() => void signOut()}>{loggingOut ? 'Logging out…' : 'Log out'}</button>
      </div>
    </section>
  )
}
