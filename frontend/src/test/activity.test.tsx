import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { App } from '../App'
import { RecommendationCard } from '../components/RecommendationCard'
import type { FavouriteGame, RecommendationItem, SearchHistory } from '../types'
import { authResponse, response } from './fixtures'

const game = {
  id: 'alpha', title: 'Alpha Quest', genres: ['RPG'], platforms: ['PC'], price_category: 'mid-range',
  short_description: 'A story-driven space adventure.',
}
const history: SearchHistory = {
  id: 'search-1', query: 'relaxing space RPG', extracted_preferences: { genres: ['RPG'], moods: ['relaxing'] },
  result_count: 4, processing_time_ms: 12.5, created_at: '2026-08-10T10:00:00Z',
}
const favourite: FavouriteGame = { id: 'fav-1', game_id: game.id, created_at: '2026-08-10T10:00:00Z', game }
const recommendation: RecommendationItem = {
  game, score: .91, explanation: 'Matches your RPG and space preferences.', matched_attributes: ['RPG', 'space'],
}

function authenticatedApp(path: string, handler: (url: string, init?: RequestInit) => Promise<Response>) {
  localStorage.setItem('gamegenie_refresh_token', 'refresh-token')
  vi.stubGlobal('fetch', vi.fn((input: string | URL | Request, init?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/refresh')) return Promise.resolve(response(authResponse))
    return handler(url, init)
  }))
  return render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>)
}

describe('user activity UI', () => {
  it('renders history and its empty state', async () => {
    authenticatedApp('/history', async url => response({ success: true, items: url.includes('history') ? [history] : [] }))
    expect(await screen.findByText('relaxing space RPG')).toBeInTheDocument()
    expect(screen.getByText(/4 results/)).toBeInTheDocument()

    localStorage.clear()
    vi.unstubAllGlobals()
    authenticatedApp('/history', async () => response({ success: true, items: [] }))
    expect(await screen.findByText('No searches yet')).toBeInTheDocument()
  })

  it('searches again and displays the returned recommendations', async () => {
    authenticatedApp('/history', async url => {
      if (url.endsWith('/api/search/recommend')) return response({ success: true, items: [recommendation], search_id: 'search-2' })
      if (url.endsWith('/api/favourites')) return response({ success: true, items: [] })
      return response({ success: true, items: [history] })
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Search Again' }))
    expect(await screen.findByText('Matches your RPG and space preferences.')).toBeInTheDocument()
  })

  it('deletes a history entry after the API succeeds', async () => {
    authenticatedApp('/history', async (url, init) => {
      if (init?.method === 'DELETE') return response({ success: true, deleted_count: 1 })
      return response({ success: true, items: [history] })
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Delete' }))
    await waitFor(() => expect(screen.queryByText('relaxing space RPG')).not.toBeInTheDocument())
  })

  it('renders favourites and removes one optimistically', async () => {
    let removeRequested = false
    authenticatedApp('/favourites', async (_url, init) => {
      if (init?.method === 'DELETE') { removeRequested = true; return response({ success: true, deleted_count: 1 }) }
      return response({ success: true, items: [favourite] })
    })
    const title = await screen.findByText('Alpha Quest')
    expect(screen.getByRole('link', { name: 'View Game' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Remove from Favourites' }))
    expect(title).not.toBeInTheDocument()
    expect(removeRequested).toBe(true)
  })

  it('adds and removes a favourite from a recommendation card', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ success: true, created: true, item: favourite }))
    vi.stubGlobal('fetch', fetchMock)
    render(<RecommendationCard item={recommendation} accessToken="access-token" />)
    await userEvent.click(screen.getByRole('button', { name: 'Add favourite' }))
    expect(await screen.findByRole('button', { name: 'Remove favourite' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Remove favourite' }))
    expect(await screen.findByRole('button', { name: 'Add favourite' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('rolls back an optimistic favourite when the API fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { message: 'Favourite service unavailable.' } }, 503)))
    render(<RecommendationCard item={recommendation} accessToken="access-token" />)
    await userEvent.click(screen.getByRole('button', { name: 'Add favourite' }))
    expect(await screen.findByRole('button', { name: 'Add favourite' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Favourite service unavailable')
  })

  it('submits recommendation feedback with the search context', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ success: true, item: { id: 'feedback-1', feedback_type: 'interested' } }, 201))
    vi.stubGlobal('fetch', fetchMock)
    render(<RecommendationCard item={recommendation} accessToken="access-token" searchId="search-1" />)
    const group = screen.getByLabelText('Feedback for Alpha Quest')
    await userEvent.click(within(group).getByRole('button', { name: 'Interested' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Feedback saved: Interested')
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(JSON.parse(String(init.body))).toMatchObject({ game_id: 'alpha', search_id: 'search-1', feedback_type: 'interested' })
  })

  it('shows personalised context and keeps score details collapsed by default', async () => {
    render(<RecommendationCard item={{ ...recommendation, base_score: 72, personalisation_score: 4, final_score: 76, personalisation_reasons: ['Similar to games in your favourites'] }} accessToken="access-token" />)
    expect(screen.getByText('Because You Liked…')).toBeInTheDocument()
    const details = screen.getByText('Why this score?').closest('details')
    expect(details).not.toHaveAttribute('open')
    await userEvent.click(screen.getByText('Why this score?'))
    expect(screen.getByText('76.0%')).toBeInTheDocument()
    expect(screen.getByText('Similar to games in your favourites')).toBeInTheDocument()
  })
})
