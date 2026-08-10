import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api, errorMessage } from '../api'
import { useAuth } from '../auth/AuthContext'
import { EmptyState, ErrorState, LoadingState } from '../components/PageState'
import { templateLabel } from '../games/types'
import type { GeneratedGame } from '../games/types'

function publicUrl(slug: string): string {
  return `${window.location.origin}/shared/${slug}`
}

export function MyGamesPage() {
  const { accessToken } = useAuth()
  const [games, setGames] = useState<GeneratedGame[]>([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState('')
  const [error, setError] = useState('')
  const [copiedId, setCopiedId] = useState('')

  useEffect(() => {
    if (!accessToken) return
    let active = true
    api.generatedGames(accessToken)
      .then(result => { if (active) setGames(result.items) })
      .catch(caught => { if (active) setError(errorMessage(caught, 'Your games could not be loaded.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [accessToken])

  async function mutate(gameId: string, operation: () => Promise<{ item: GeneratedGame }>) {
    setBusyId(gameId); setError('')
    try {
      const result = await operation()
      setGames(items => items.map(item => item.id === gameId ? result.item : item))
      setCopiedId('')
    } catch (caught) {
      setError(errorMessage(caught, 'The generated game could not be updated.'))
    } finally {
      setBusyId('')
    }
  }

  async function remove(game: GeneratedGame) {
    if (!accessToken || !window.confirm(`Delete ${game.title}? This cannot be undone.`)) return
    setBusyId(game.id); setError('')
    try {
      await api.deleteGeneratedGame(accessToken, game.id)
      setGames(items => items.filter(item => item.id !== game.id))
    } catch (caught) {
      setError(errorMessage(caught, 'The generated game could not be deleted.'))
    } finally {
      setBusyId('')
    }
  }

  async function copyLink(game: GeneratedGame) {
    if (!game.public_slug) return
    try {
      await navigator.clipboard.writeText(publicUrl(game.public_slug))
      setCopiedId(game.id)
    } catch {
      setError('The share link could not be copied. You can copy it from the link field instead.')
    }
  }

  if (loading) return <LoadingState message="Loading your generated games…" />

  return <section><div className="section-heading"><div><p className="eyebrow">Your creations</p><h1>My games</h1></div><Link className="button-link" to="/generator">Generate a game</Link></div>
    {error && <ErrorState message={error} />}
    {!error && (games.length === 0 ? <EmptyState title="No saved games yet" message="Generate a game, then save it to reopen or share later." action={<Link className="button-link" to="/generator">Generate a game</Link>} /> :
      <div className="game-grid">{games.map(game => <article className="card activity-card" key={game.id}>
        <div className="card-heading"><div><h2>{game.title}</h2><p className="meta">{templateLabel(game.template_type)} · Created {new Date(game.created_at).toLocaleDateString()}</p></div><span className={`visibility-badge ${game.is_public ? 'public' : ''}`}>{game.is_public ? 'Public' : 'Private'}</span></div>
        {game.migrated_from_version && <p className="warning">Compatible configuration migrated from {game.migrated_from_version}.</p>}
        <div className="actions">
          <Link className="button-link compact" to={`/play/saved/${game.id}`}>Play</Link>
          <Link className="button-link compact secondary" to={`/generator?saved=${game.id}`}>Edit Settings</Link>
          {!game.is_public && <button className="compact secondary" disabled={busyId === game.id} aria-label={`Share ${game.title}`} onClick={() => accessToken && void mutate(game.id, () => api.shareGeneratedGame(accessToken, game.id))}>{busyId === game.id ? 'Sharing…' : 'Share'}</button>}
          {game.is_public && <button className="compact secondary" disabled={busyId === game.id} aria-label={`Unshare ${game.title}`} onClick={() => accessToken && void mutate(game.id, () => api.unshareGeneratedGame(accessToken, game.id))}>{busyId === game.id ? 'Unsharing…' : 'Unshare'}</button>}
          <button className="compact danger" disabled={busyId === game.id} aria-label={`Delete ${game.title}`} onClick={() => void remove(game)}>Delete</button>
        </div>
        {game.is_public && game.public_slug && <div className="share-row"><Link to={`/shared/${game.public_slug}`}>{publicUrl(game.public_slug)}</Link><button className="compact secondary" aria-label={`Copy share link for ${game.title}`} onClick={() => void copyLink(game)}>{copiedId === game.id ? 'Copied' : 'Copy link'}</button></div>}
      </article>)}</div>)}
  </section>
}
