import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { expect, it, vi } from 'vitest'

import { App } from '../App'
import { authResponse, preferences, response } from './fixtures'

it('loads and saves controlled preferences', async () => {
  localStorage.setItem('gamegenie_refresh_token', 'stored-refresh')
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(response(authResponse))
    .mockResolvedValueOnce(response({ success: true, preferences }))
    .mockResolvedValueOnce(response({ success: true, preferences: { ...preferences, preferred_genres: ['strategy'] } }))
  vi.stubGlobal('fetch', fetchMock)
  render(<MemoryRouter initialEntries={['/preferences']}><App /></MemoryRouter>)

  expect(await screen.findByRole('heading', { name: 'Your preferences' })).toBeInTheDocument()
  await userEvent.click(screen.getByLabelText('strategy'))
  await userEvent.click(screen.getByRole('button', { name: 'Save preferences' }))
  expect(await screen.findByText('Preferences saved.')).toBeInTheDocument()
  const putCall = fetchMock.mock.calls.find((call) => (call[1] as RequestInit | undefined)?.method === 'PUT')
  expect(putCall).toBeDefined()
  expect((putCall?.[1] as RequestInit).body).toContain('strategy')
})
