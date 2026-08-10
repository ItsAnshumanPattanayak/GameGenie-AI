import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { errorMessage } from '../api'
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
      const requestedTarget = (location.state as { from?: string } | null)?.from
      const target = requestedTarget?.startsWith('/') ? requestedTarget : '/dashboard'
      navigate(target, { replace: true })
    } catch (reason) {
      setError(errorMessage(reason, 'Login failed. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-shell">
      <form className="card auth-card" onSubmit={submit} noValidate>
        <p className="eyebrow">Welcome back</p>
        <h1>Log in to GameGenie</h1>
        <label htmlFor="email"><span>Email</span><input id="email" name="email" type="email" autoComplete="email" required aria-describedby={error ? 'login-error' : undefined} value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <PasswordField id="password" name="password" label="Password" autoComplete="current-password" required aria-describedby={error ? 'login-error' : undefined} value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p id="login-error" className="error" role="alert">{error}</p>}
        <button type="submit" disabled={loading}>{loading ? 'Logging in…' : 'Log in'}</button>
        <p>New here? <Link to="/register">Create an account</Link></p>
      </form>
    </main>
  )
}
