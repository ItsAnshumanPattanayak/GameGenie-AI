import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api, errorMessage } from '../api'
import { ErrorState, LoadingState } from '../components/PageState'
import { GameHost } from '../games/GameHost'
import { templateLabel, type PublicGeneratedGame } from '../games/types'

export function PublicSharedGamePage() {
  const { slug = '' } = useParams()
  const [game, setGame] = useState<PublicGeneratedGame | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    api.publicGeneratedGame(slug)
      .then(result => { if (active) setGame(result.item) })
      .catch(caught => { if (active) setError(errorMessage(caught, 'This shared game is unavailable.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [slug])

  if (loading) return <main className="app-shell"><LoadingState message="Loading shared game…" /></main>
  if (error || !game) return <main className="app-shell"><section><h1>Shared game unavailable</h1><ErrorState message={error || 'The link is invalid, private, or no longer active.'} action={<Link className="button-link" to="/register">Create your own game</Link>} /></section></main>
  return <main className="app-shell"><section><Link className="brand public-brand" to="/login">Game<span>Genie</span> AI</Link><p className="eyebrow">Shared GameGenie creation</p><h1>{game.title}</h1><p className="meta">{templateLabel(game.template_type)} · Read-only public game</p>{game.migrated_from_version && <p className="warning">Loaded with compatible configuration defaults.</p>}<GameHost configuration={game.configuration} /><div className="public-cta card"><h2>Want to build your own?</h2><Link className="button-link" to="/register">Create your own game</Link></div></section></main>
}
