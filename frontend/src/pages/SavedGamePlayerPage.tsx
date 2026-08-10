import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api, errorMessage } from '../api'
import { useAuth } from '../auth/AuthContext'
import { ErrorState, LoadingState } from '../components/PageState'
import { GameHost } from '../games/GameHost'
import { templateLabel, type GeneratedGame } from '../games/types'

export function SavedGamePlayerPage() {
  const { id = '' } = useParams()
  const { accessToken } = useAuth()
  const [game, setGame] = useState<GeneratedGame | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!accessToken) return
    let active = true
    api.generatedGame(accessToken, id)
      .then(result => { if (active) setGame(result.item) })
      .catch(caught => { if (active) setError(errorMessage(caught, 'The saved game could not be loaded.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [accessToken, id])

  if (loading) return <LoadingState message="Loading saved game…" />
  if (error || !game) return <section><h1>Saved game unavailable</h1><ErrorState message={error || 'The saved game could not be loaded.'} action={<Link className="button-link secondary" to="/my-games">Back to My Games</Link>} /></section>
  return <section><p className="eyebrow">Saved game</p><h1>{game.title}</h1><p className="meta">{templateLabel(game.template_type)} · Configuration {game.config_version}</p>{game.migrated_from_version && <p className="warning">Loaded safely from configuration {game.migrated_from_version}.</p>}<GameHost configuration={game.configuration} /><div className="actions"><Link className="button-link secondary" to="/my-games">Back to My Games</Link><Link className="button-link" to={`/generator?saved=${game.id}`}>Edit Settings</Link></div></section>
}
