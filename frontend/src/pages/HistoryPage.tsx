import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, errorMessage } from '../api'
import { useAuth } from '../auth/AuthContext'
import { EmptyState, ErrorState, LoadingState } from '../components/PageState'
import type { SearchHistory } from '../types'

function preferenceSummary(values: Record<string, unknown>): string {
  const entries = Object.entries(values).filter(([, value]) => value !== null && value !== '' && (!Array.isArray(value) || value.length))
  return entries.length ? entries.map(([key, value]) => `${key.replaceAll('_', ' ')}: ${Array.isArray(value) ? value.join(', ') : String(value)}`).join(' · ') : 'No controlled preferences extracted'
}

export function HistoryPage() {
  const { accessToken } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState<SearchHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!accessToken) return
    api.searchHistory(accessToken).then(data => setItems(data.items)).catch(caught => setError(errorMessage(caught, 'Could not load search history.'))).finally(() => setLoading(false))
  }, [accessToken])

  async function searchAgain(item: SearchHistory) {
    if (!accessToken) return
    setBusyId(item.id)
    setError('')
    try {
      const recommendation = await api.recommend(item.query, accessToken)
      navigate('/dashboard', { state: { recommendation } })
    } catch (caught) {
      setError(errorMessage(caught, 'Could not repeat this search.'))
      setBusyId(null)
    }
  }

  async function remove(item: SearchHistory) {
    if (!accessToken) return
    setBusyId(item.id)
    setError('')
    try {
      await api.deleteSearchHistory(accessToken, item.id)
      setItems(current => current.filter(entry => entry.id !== item.id))
    } catch (caught) {
      setError(errorMessage(caught, 'Could not delete this search.'))
    } finally {
      setBusyId(null)
    }
  }

  return <section><p className="eyebrow">Your activity</p><h1>Search history</h1>
    {loading && <LoadingState message="Loading search history…" />}
    {error && <ErrorState message={error} />}
    {!loading && !error && items.length === 0 && <EmptyState title="No searches yet" message="Authenticated recommendations will appear here." />}
    {!loading && !error && <div className="activity-list">{items.map(item => <article className="card activity-card" key={item.id}>
      <div className="card-heading"><div><h2>{item.query}</h2><p className="meta">{new Date(item.created_at).toLocaleString()} · {item.result_count} results</p></div></div>
      <p>{preferenceSummary(item.extracted_preferences)}</p>
      <div className="actions"><button disabled={busyId === item.id} aria-label={`Search again for ${item.query}`} onClick={() => void searchAgain(item)}>{busyId === item.id ? 'Working…' : 'Search Again'}</button><button className="secondary" disabled={busyId === item.id} aria-label={`Delete search ${item.query}`} onClick={() => void remove(item)}>Delete</button></div>
    </article>)}</div>}
  </section>
}
