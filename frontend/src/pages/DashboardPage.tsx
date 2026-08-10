import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { api, errorMessage } from '../api'
import { useAuth } from '../auth/AuthContext'
import { ErrorState, LoadingState } from '../components/PageState'
import { RecommendationCard } from '../components/RecommendationCard'
import { templateLabel, type GeneratedGame } from '../games/types'
import type { FavouriteGame, RecommendationResponse, SearchHistory } from '../types'

interface DashboardState { recommendation?: RecommendationResponse }

export function DashboardPage() {
  const { currentUser, accessToken } = useAuth()
  const location = useLocation()
  const recommendation = (location.state as DashboardState | null)?.recommendation
  const [history, setHistory] = useState<SearchHistory[]>([])
  const [favourites, setFavourites] = useState<FavouriteGame[]>([])
  const [generatedGames, setGeneratedGames] = useState<GeneratedGame[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!accessToken) return
    Promise.all([api.searchHistory(accessToken), api.favourites(accessToken), api.generatedGames(accessToken)])
      .then(([searches, favouriteGames, savedGames]) => { setHistory(searches.items.slice(0, 3)); setFavourites(favouriteGames.items.slice(0, 3)); setGeneratedGames(savedGames.items.slice(0, 3)) })
      .catch(caught => setError(errorMessage(caught, 'Could not load dashboard activity.')))
      .finally(() => setLoading(false))
  }, [accessToken])

  const favouriteIds = new Set(favourites.map(item => item.game_id))
  return <section><p className="eyebrow">Dashboard</p><h1>Welcome, {currentUser?.name}</h1>
    {loading && <LoadingState message="Loading your dashboard…" />}{error && <ErrorState message={error} />}
    {!loading && !error && <div className="dashboard-grid">
      <section className="card dashboard-section wide"><div className="section-heading"><h2>Recommended for You</h2></div>
        {recommendation?.items.length ? <div className="recommendation-list">{recommendation.items.map(item => <RecommendationCard key={item.game.id} item={item} accessToken={accessToken ?? ''} searchId={recommendation.search_id} initiallyFavourite={favouriteIds.has(item.game.id)} />)}</div> : <p className="inline-empty">Search again from your history to see recommendations shaped by your preferences and activity.</p>}
      </section>
      <section className="card dashboard-section"><div className="section-heading"><h2>Recent Searches</h2><Link to="/history">View all</Link></div>{history.length ? history.map(item => <p key={item.id}><strong>{item.query}</strong><br/><span className="meta">{item.result_count} results</span></p>) : <p className="meta">No recent searches.</p>}</section>
      <section className="card dashboard-section"><div className="section-heading"><h2>Favourite Games</h2><Link to="/favourites">View all</Link></div>{favourites.length ? favourites.map(item => <p key={item.id}><strong>{item.game.title}</strong></p>) : <p className="meta">No favourite games.</p>}</section>
      <section className="card dashboard-section wide"><div className="section-heading"><h2>Recently Generated Games</h2><Link to="/my-games">View all</Link></div>{generatedGames.length ? <div className="compact-list">{generatedGames.map(game => <Link key={game.id} to={`/play/saved/${game.id}`}><strong>{game.title}</strong><span className="meta">{templateLabel(game.template_type)}</span></Link>)}</div> : <p className="inline-empty">No saved games yet. <Link to="/generator">Generate your first game.</Link></p>}</section>
    </div>
    }
  </section>
}
