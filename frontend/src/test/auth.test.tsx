import { StrictMode } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { App } from '../App'
import { AuthProvider, useAuth } from '../auth/AuthContext'
import { authResponse, response } from './fixtures'

function renderApp(path: string) {
  return render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>)
}

describe('authentication UI', () => {
  it('validates the registration form before calling the API', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    renderApp('/register')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Enter your name')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('registers and redirects to the protected dashboard', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response(authResponse, 201))
    vi.stubGlobal('fetch', fetchMock)
    renderApp('/register')
    await userEvent.type(screen.getByLabelText('Name'), 'Player One')
    await userEvent.type(screen.getByLabelText('Email'), 'player@example.com')
    await userEvent.type(screen.getByLabelText('Password', { selector: '#password' }), 'StrongPass123')
    await userEvent.type(screen.getByLabelText('Confirm password'), 'StrongPass123')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByText('Welcome, Player One')).toBeInTheDocument()
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:8000/api/auth/register')
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(init.method).toBe('POST')
    expect(new Headers(init.headers).get('Content-Type')).toBe('application/json')
    expect(JSON.parse(String(init.body))).toEqual({ name: 'Player One', email: 'player@example.com', password: 'StrongPass123' })
  })

  it('shows a useful message when the backend cannot be reached', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    renderApp('/register')
    await userEvent.type(screen.getByLabelText('Name'), 'Player One')
    await userEvent.type(screen.getByLabelText('Email'), 'player@example.com')
    await userEvent.type(screen.getByLabelText('Password', { selector: '#password' }), 'StrongPass123')
    await userEvent.type(screen.getByLabelText('Confirm password'), 'StrongPass123')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the GameGenie backend')
    expect(screen.getByRole('alert')).not.toHaveTextContent('Failed to fetch')
  })

  it('shows a registration error returned by the backend', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { code: 'EMAIL_ALREADY_REGISTERED', message: 'An account with this email already exists.' } }, 409)))
    renderApp('/register')
    await userEvent.type(screen.getByLabelText('Name'), 'Player One')
    await userEvent.type(screen.getByLabelText('Email'), 'player@example.com')
    await userEvent.type(screen.getByLabelText('Password', { selector: '#password' }), 'StrongPass123')
    await userEvent.type(screen.getByLabelText('Confirm password'), 'StrongPass123')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('account with this email already exists')
  })

  it('logs in and establishes authenticated state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(authResponse)))
    renderApp('/login')
    await userEvent.type(screen.getByLabelText('Email'), 'player@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'StrongPass123')
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    expect(await screen.findByText('Welcome, Player One')).toBeInTheDocument()
    expect(localStorage.getItem('gamegenie_refresh_token')).toBe('refresh-token')
  })

  it('displays invalid credentials returned by the API', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { code: 'INVALID_CREDENTIALS', message: 'The email or password is incorrect.' } }, 401)))
    renderApp('/login')
    await userEvent.type(screen.getByLabelText('Email'), 'player@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'WrongPass123')
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('email or password is incorrect')
  })

  it('logs out and clears authentication state', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(response(authResponse)).mockResolvedValueOnce(response({ success: true }))
    vi.stubGlobal('fetch', fetchMock)
    function Harness() {
      const auth = useAuth()
      return <><span>{auth.isAuthenticated ? auth.currentUser?.name : 'anonymous'}</span><button onClick={() => void auth.login('player@example.com', 'StrongPass123')}>Sign in</button><button onClick={() => void auth.logout()}>Sign out</button></>
    }
    render(<AuthProvider><Harness /></AuthProvider>)
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Player One')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    await waitFor(() => expect(screen.getByText('anonymous')).toBeInTheDocument())
    expect(localStorage.getItem('gamegenie_refresh_token')).toBeNull()
  })

  it('redirects an anonymous visitor away from a protected route', async () => {
    renderApp('/profile')
    expect(await screen.findByRole('heading', { name: 'Log in to GameGenie' })).toBeInTheDocument()
  })

  it('restores one session without flashing protected content in StrictMode', async () => {
    localStorage.setItem('gamegenie_refresh_token', 'stored-refresh')
    let resolveRefresh!: (value: Response) => void
    const fetchMock = vi.fn(() => new Promise<Response>(resolve => { resolveRefresh = resolve }))
    vi.stubGlobal('fetch', fetchMock)
    render(<StrictMode><MemoryRouter initialEntries={['/profile']}><App /></MemoryRouter></StrictMode>)
    expect(screen.getByRole('status')).toHaveTextContent('Restoring your session')
    expect(screen.queryByRole('heading', { name: 'Player One' })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Log in to GameGenie' })).not.toBeInTheDocument()
    resolveRefresh(response(authResponse))
    expect(await screen.findByRole('heading', { name: 'Player One' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
