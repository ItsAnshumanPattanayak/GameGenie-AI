import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { errorMessage } from '../api'
import { useAuth } from '../auth/AuthContext'
import { PasswordField } from '../components/PasswordField'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (name.trim().length < 2) return setError('Enter your name.')
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError('Enter a valid email address.')
    if (password.length < 10 || !/[a-z]/.test(password) || !/[A-Z]/.test(password) || !/\d/.test(password)) {
      return setError('Use at least 10 characters with uppercase, lowercase, and a number.')
    }
    if (password !== confirmPassword) return setError('Passwords do not match.')
    setError('')
    setLoading(true)
    try {
      await register(name.trim(), email.trim(), password)
      navigate('/dashboard', { replace: true })
    } catch (reason) {
      setError(errorMessage(reason, 'Registration failed. Please try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-shell">
      <form className="card auth-card" onSubmit={submit} noValidate>
        <p className="eyebrow">Create your player profile</p>
        <h1>Join GameGenie</h1>
        <label htmlFor="name"><span>Name</span><input id="name" name="name" autoComplete="name" required aria-describedby={error ? 'registration-error' : undefined} value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label htmlFor="email"><span>Email</span><input id="email" name="email" type="email" autoComplete="email" required aria-describedby={error ? 'registration-error' : undefined} value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <PasswordField id="password" name="password" label="Password" autoComplete="new-password" required aria-describedby={error ? 'registration-error' : undefined} value={password} onChange={(e) => setPassword(e.target.value)} />
        <PasswordField id="confirm-password" name="confirm-password" label="Confirm password" autoComplete="new-password" required aria-describedby={error ? 'registration-error' : undefined} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
        {error && <p id="registration-error" className="error" role="alert">{error}</p>}
        <button type="submit" disabled={loading}>{loading ? 'Creating account…' : 'Create account'}</button>
        <p>Already registered? <Link to="/login">Log in</Link></p>
      </form>
    </main>
  )
}
