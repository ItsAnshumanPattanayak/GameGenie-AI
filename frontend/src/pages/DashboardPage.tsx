import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { api } from '../api'
import { useAuth } from '../auth/AuthContext'
import { RecommendationCard } from '../components/RecommendationCard'
import type { FavouriteGame, RecommendationResponse, SearchHistory } from '../types'

interface DashboardState { recommendation?: RecommendationResponse }

export function DashboardPage() {
  const { currentUser, accessToken } = useAuth()
  const location = useLocation()
  const recommendation = (location.state as DashboardState | null)?.recommendation
  const [history, setHistory] = useState<SearchHistory[]>([])
  const [favourites, setFavourites] = useState<FavouriteGame[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!accessToken) return
    Promise.all([api.searchHistory(accessToken), api.favourites(accessToken)])
      .then(([searches, favouriteGames]) => { setHistory(searches.items.slice(0, 3)); setFavourites(favouriteGames.items.slice(0, 3)) })
      .catch(caught => setError(caught instanceof Error ? caught.message : 'Could not load dashboard activity.'))
      .finally(() => setLoading(false))
  }, [accessToken])

  const favouriteIds = new Set(favourites.map(item => item.game_id))
  return <section><p className="eyebrow">Dashboard</p><h1>Welcome, {currentUser?.name}</h1>
    {loading && <p role="status">Loading your activity…</p>}{error && <p className="error" role="alert">{error}</p>}
    <div className="dashboard-grid">
      <section className="card dashboard-section wide"><div className="section-heading"><h2>Recommended for You</h2></div>
        {recommendation?.items.length ? recommendation.items.map(item => <RecommendationCard key={item.game.id} item={item} accessToken={accessToken ?? ''} searchId={recommendation.search_id} initiallyFavourite={favouriteIds.has(item.game.id)} />) : <p className="meta">Search again from your history to see recommendations shaped by your preferences and activity.</p>}
      </section>
      <section className="card dashboard-section"><div className="section-heading"><h2>Recent Searches</h2><Link to="/history">View all</Link></div>{history.length ? history.map(item => <p key={item.id}><strong>{item.query}</strong><br/><span className="meta">{item.result_count} results</span></p>) : <p className="meta">No recent searches.</p>}</section>
      <section className="card dashboard-section"><div className="section-heading"><h2>Favourite Games</h2><Link to="/favourites">View all</Link></div>{favourites.length ? favourites.map(item => <p key={item.id}><strong>{item.game.title}</strong></p>) : <p className="meta">No favourite games.</p>}</section>
      <section className="card dashboard-section"><h2>Recently Generated Games</h2><p className="meta">Generation history will connect here in a later phase.</p></section>
      <section className="card dashboard-section"><h2>Continue Playing</h2><p className="meta">Saved play sessions will connect here in a later phase.</p></section>
    </div>
  </section>
}
