import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { GameConfiguration, GeneratedGame } from '../games/types'

vi.mock('../games/GameHost', () => ({
  GameHost: ({ configuration }: { configuration: GameConfiguration }) =>
    <div data-testid="game-host">Playing {configuration.template}: {configuration.title}</div>,
}))

import { App } from '../App'
import { authResponse, response } from './fixtures'

const configurations: Record<string, GameConfiguration> = {
  space_shooter: {
    template: 'space_shooter', title: 'Saved Stars', theme: 'space', difficulty: 'medium',
    player_speed: 7, enemy_speed: 4, enemy_spawn_interval: 2, lives: 3, difficulty_scaling: false,
  },
  endless_runner: {
    template: 'endless_runner', title: 'Saved Dash', theme: 'neon', difficulty: 'hard',
    player_speed: 11, jump_force: 780, obstacle_frequency: .8, difficulty_scaling: true,
  },
  maze_escape: {
    template: 'maze_escape', title: 'Saved Maze', theme: 'jungle', difficulty: 'hard',
    maze_size: 25, time_limit: 45, obstacle_count: 14,
  },
}

function savedGame(template = 'space_shooter', updates: Partial<GeneratedGame> = {}): GeneratedGame {
  const configuration = configurations[template]
  return {
    id: `saved-${template}`,
    title: configuration.title,
    prompt: `a ${template.replaceAll('_', ' ')}`,
    template_type: configuration.template,
    configuration,
    config_version: '1.1',
    migrated_from_version: null,
    public_slug: null,
    is_public: false,
    created_at: '2026-08-10T10:00:00Z',
    updated_at: '2026-08-10T10:00:00Z',
    ...updates,
  }
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

describe('generated-game persistence UI', () => {
  it('renders the library and its empty state', async () => {
    authenticatedApp('/my-games', async () => response({ success: true, items: [savedGame()] }))
    expect(await screen.findByText('Saved Stars')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Play' })).toHaveAttribute('href', '/play/saved/saved-space_shooter')
    expect(screen.getByRole('link', { name: 'Edit Settings' })).toHaveAttribute('href', '/generator?saved=saved-space_shooter')

    localStorage.clear(); vi.unstubAllGlobals()
    authenticatedApp('/my-games', async () => response({ success: true, items: [] }))
    expect(await screen.findByText('No saved games yet')).toBeInTheDocument()
  })

  it('shares and unshares a saved game', async () => {
    const privateGame = savedGame()
    const publicGame = savedGame('space_shooter', { is_public: true, public_slug: 'a-unique-public-slug-value-1234' })
    authenticatedApp('/my-games', async (url) => {
      if (url.endsWith('/share')) return response({ success: true, item: publicGame })
      if (url.endsWith('/unshare')) return response({ success: true, item: privateGame })
      return response({ success: true, items: [privateGame] })
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Share' }))
    expect(await screen.findByText('Public')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /a-unique-public-slug/ })).toHaveAttribute(
      'href', expect.stringContaining('/shared/a-unique-public-slug-value-1234'),
    )
    await userEvent.click(screen.getByRole('button', { name: 'Unshare' }))
    expect(await screen.findByText('Private')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /a-unique-public-slug/ })).not.toBeInTheDocument()
  })

  it('confirms and deletes a saved game', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    let deleted = false
    authenticatedApp('/my-games', async (_url, init) => {
      if (init?.method === 'DELETE') { deleted = true; return response({ success: true, deleted_id: 'saved-space_shooter' }) }
      return response({ success: true, items: [savedGame()] })
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Delete' }))
    await waitFor(() => expect(screen.queryByText('Saved Stars')).not.toBeInTheDocument())
    expect(deleted).toBe(true)
  })

  it.each(['space_shooter', 'endless_runner', 'maze_escape'])('reopens and dispatches %s', async template => {
    const item = savedGame(template)
    authenticatedApp(`/play/saved/${item.id}`, async () => response({ success: true, item }))
    expect(await screen.findByTestId('game-host')).toHaveTextContent(`Playing ${template}`)
    expect(screen.getByText(item.title, { selector: 'h1' })).toBeInTheDocument()
  })

  it('renders a public shared game without authentication', async () => {
    const item = savedGame('maze_escape', { public_slug: 'public-maze-slug-value-123456', is_public: true })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ success: true, item })))
    render(<MemoryRouter initialEntries={['/shared/public-maze-slug-value-123456']}><App /></MemoryRouter>)
    expect(await screen.findByTestId('game-host', {}, { timeout: 5000 })).toHaveTextContent('Playing maze_escape')
    expect(screen.getByRole('link', { name: 'Create Your Own Game' })).toHaveAttribute('href', '/register')
  })

  it.each(['invalid slug', 'private game'])('shows the unavailable state for %s', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { code: 'PUBLIC_GAME_NOT_FOUND', message: 'The shared game is unavailable.' } }, 404)))
    render(<MemoryRouter initialEntries={['/shared/unavailable-slug-value-12345']}><App /></MemoryRouter>)
    expect(await screen.findByRole('heading', { name: 'Shared game unavailable' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('shared game is unavailable')
  })
})
