import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api, errorMessage } from '../api'
import { useAuth } from '../auth/AuthContext'
import { EmptyState, ErrorState, LoadingState } from '../components/PageState'
import type { FavouriteGame } from '../types'

export function FavouritesPage() {
  const { accessToken } = useAuth()
  const [items, setItems] = useState<FavouriteGame[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!accessToken) return
    api.favourites(accessToken).then(data => setItems(data.items)).catch(caught => setError(errorMessage(caught, 'Could not load favourites.'))).finally(() => setLoading(false))
  }, [accessToken])

  async function remove(item: FavouriteGame) {
    if (!accessToken) return
    const index = items.findIndex(entry => entry.id === item.id)
    setItems(current => current.filter(entry => entry.id !== item.id))
    setError('')
    try {
      await api.removeFavourite(accessToken, item.game_id)
    } catch (caught) {
      setItems(current => [...current.slice(0, index), item, ...current.slice(index)])
      setError(errorMessage(caught, 'Could not remove this favourite.'))
    }
  }

  return <section><p className="eyebrow">Your library</p><h1>Favourite games</h1>
    {loading && <LoadingState message="Loading favourites…" />}
    {error && <ErrorState message={error} />}
    {!loading && !error && items.length === 0 && <EmptyState title="No favourites yet" message="Add games from recommendation cards to see them here." />}
    {!loading && !error && <div className="game-grid">{items.map(item => <article className="card activity-card" key={item.id}>
      <h2>{item.game.title}</h2><p>{item.game.short_description ?? item.game.description ?? 'No description available.'}</p>
      <p className="meta">{item.game.genres.join(' · ')} · {item.game.platforms.join(' · ')}</p>
      <div className="actions"><Link className="button-link secondary" to={`/generator?game=${encodeURIComponent(item.game_id)}`}>Generate Similar Game</Link><button className="secondary" aria-label={`Remove ${item.game.title} from favourites`} onClick={() => void remove(item)}>Remove from Favourites</button></div>
    </article>)}</div>}
  </section>
}
