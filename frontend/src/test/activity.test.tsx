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
  it('renders the dashboard search form and validates short queries', async () => {
    let recommendationRequested = false
    authenticatedApp('/dashboard', async url => {
      if (url.endsWith('/api/search/recommend')) recommendationRequested = true
      return response({ success: true, items: [] })
    })

    expect(await screen.findByRole('heading', { name: 'Find Your Next Game' })).toBeInTheDocument()
    expect(screen.getByLabelText('What would you like to play?')).toHaveAttribute(
      'placeholder',
      'A futuristic multiplayer shooter for PC with fast combat',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Recommend games' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('at least 3 characters')
    expect(recommendationRequested).toBe(false)
  })

  it('searches from the dashboard, renders personalised results, and refreshes recent searches', async () => {
    let historyRequests = 0
    let releaseRecommendation: () => void = () => undefined
    const recommendationPending = new Promise<void>(resolve => { releaseRecommendation = resolve })
    let recommendationInit: RequestInit | undefined
    const newHistory = { ...history, id: 'search-2', query: 'A futuristic multiplayer shooter for PC' }
    authenticatedApp('/dashboard', async (url, init) => {
      if (url.endsWith('/api/search/recommend')) {
        recommendationInit = init
        await recommendationPending
        return response({
          success: true,
          items: [{
            ...recommendation,
            base_score: 72,
            personalisation_score: 4,
            final_score: 76,
            personalisation_reasons: ['Similar to games in your favourites'],
          }],
          search_id: 'search-2',
        })
      }
      if (url.endsWith('/api/history/searches')) {
        historyRequests += 1
        return response({ success: true, items: historyRequests > 1 ? [newHistory] : [] })
      }
      return response({ success: true, items: [] })
    })

    expect(await screen.findByText('No recent searches.')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('What would you like to play?'), `  ${newHistory.query}  `)
    await userEvent.click(screen.getByRole('button', { name: 'Recommend games' }))
    expect(screen.getByRole('button', { name: 'Finding games…' })).toBeDisabled()
    releaseRecommendation()

    expect(await screen.findByText('Matches your RPG and space preferences.')).toBeInTheDocument()
    expect(screen.getByText(/Because You Liked/)).toBeInTheDocument()
    expect(await screen.findByText(newHistory.query)).toBeInTheDocument()
    expect(historyRequests).toBe(2)
    expect(new Headers(recommendationInit?.headers).get('Authorization')).toBe('Bearer access-token')
    expect(JSON.parse(String(recommendationInit?.body))).toEqual({ prompt: newHistory.query, limit: 10 })
  })

  it('shows a backend recommendation error on the dashboard', async () => {
    authenticatedApp('/dashboard', async url => {
      if (url.endsWith('/api/search/recommend')) {
        return response({ error: { code: 'AI_SERVICE_UNAVAILABLE', message: 'Recommendations are temporarily unavailable.' } }, 503)
      }
      return response({ success: true, items: [] })
    })
    await screen.findByText('No recent searches.')
    await userEvent.type(screen.getByLabelText('What would you like to play?'), 'multiplayer shooter')
    await userEvent.click(screen.getByRole('button', { name: 'Recommend games' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Recommendations are temporarily unavailable')
  })

  it('shows the shared network error when dashboard search cannot reach the backend', async () => {
    authenticatedApp('/dashboard', async url => {
      if (url.endsWith('/api/search/recommend')) throw new TypeError('Failed to fetch')
      return response({ success: true, items: [] })
    })
    await screen.findByText('No recent searches.')
    await userEvent.type(screen.getByLabelText('What would you like to play?'), 'multiplayer shooter')
    await userEvent.click(screen.getByRole('button', { name: 'Recommend games' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the GameGenie backend')
  })

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
    await userEvent.click(await screen.findByRole('button', { name: 'Search again for relaxing space RPG' }))
    expect(await screen.findByText('Matches your RPG and space preferences.')).toBeInTheDocument()
  })

  it('deletes a history entry after the API succeeds', async () => {
    authenticatedApp('/history', async (url, init) => {
      if (init?.method === 'DELETE') return response({ success: true, deleted_count: 1 })
      return response({ success: true, items: [history] })
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Delete search relaxing space RPG' }))
    await waitFor(() => expect(screen.queryByText('relaxing space RPG')).not.toBeInTheDocument())
  })

  it('renders favourites and removes one optimistically', async () => {
    let removeRequested = false
    authenticatedApp('/favourites', async (_url, init) => {
      if (init?.method === 'DELETE') { removeRequested = true; return response({ success: true, deleted_count: 1 }) }
      return response({ success: true, items: [favourite] })
    })
    const title = await screen.findByText('Alpha Quest')
    expect(screen.getByRole('link', { name: 'Generate Similar Game' })).toHaveAttribute('href', '/generator?game=alpha')
    await userEvent.click(screen.getByRole('button', { name: 'Remove Alpha Quest from favourites' }))
    expect(title).not.toBeInTheDocument()
    expect(removeRequested).toBe(true)
  })

  it('adds and removes a favourite from a recommendation card', async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ success: true, created: true, item: favourite }))
    vi.stubGlobal('fetch', fetchMock)
    render(<RecommendationCard item={recommendation} accessToken="access-token" />)
    await userEvent.click(screen.getByRole('button', { name: 'Add Alpha Quest to favourites' }))
    expect(await screen.findByRole('button', { name: 'Remove Alpha Quest from favourites' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Remove Alpha Quest from favourites' }))
    expect(await screen.findByRole('button', { name: 'Add Alpha Quest to favourites' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('rolls back an optimistic favourite when the API fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { message: 'Favourite service unavailable.' } }, 503)))
    render(<RecommendationCard item={recommendation} accessToken="access-token" />)
    await userEvent.click(screen.getByRole('button', { name: 'Add Alpha Quest to favourites' }))
    expect(await screen.findByRole('button', { name: 'Add Alpha Quest to favourites' })).toBeInTheDocument()
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
