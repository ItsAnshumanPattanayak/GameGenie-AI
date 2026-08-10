import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '../api'
import { useAuth } from '../auth/AuthContext'
import { PasswordField } from '../components/PasswordField'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!email || !password) return setError('Enter your email and password.')
    setError('')
    setLoading(true)
    try {
      await login(email.trim(), password)
      const target = (location.state as { from?: string } | null)?.from ?? '/dashboard'
      navigate(target, { replace: true })
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-shell">
      <form className="card auth-card" onSubmit={submit} noValidate>
        <p className="eyebrow">Welcome back</p>
        <h1>Log in to GameGenie</h1>
        <label htmlFor="email"><span>Email</span><input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <PasswordField id="password" label="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" disabled={loading}>{loading ? 'Logging in…' : 'Log in'}</button>
        <p>New here? <Link to="/register">Create an account</Link></p>
      </form>
    </main>
  )
}
