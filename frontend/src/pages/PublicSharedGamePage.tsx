import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api } from '../api'
import { GameHost } from '../games/GameHost'
import type { PublicGeneratedGame } from '../games/types'

export function PublicSharedGamePage() {
  const { slug = '' } = useParams()
  const [game, setGame] = useState<PublicGeneratedGame | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    api.publicGeneratedGame(slug)
      .then(result => { if (active) setGame(result.item) })
      .catch(caught => { if (active) setError(caught instanceof Error ? caught.message : 'This shared game is unavailable.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [slug])

  if (loading) return <main className="app-shell"><p role="status">Loading shared game…</p></main>
  if (error || !game) return <main className="app-shell"><section className="card empty-state"><h1>Shared game unavailable</h1><p className="error" role="alert">{error || 'The link is invalid, private, or no longer active.'}</p><Link className="button-link" to="/register">Create Your Own Game</Link></section></main>
  return <main className="app-shell"><section><p className="eyebrow">Shared GameGenie creation</p><h1>{game.title}</h1><p className="meta">{game.template_type.replaceAll('_', ' ')} · Read-only public game</p>{game.migrated_from_version && <p className="warning">Loaded with compatible configuration defaults.</p>}<GameHost configuration={game.configuration} /><div className="public-cta card"><h2>Want to build your own?</h2><Link className="button-link" to="/register">Create Your Own Game</Link></div></section></main>
}
