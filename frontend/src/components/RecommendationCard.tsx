import { useState } from 'react'

import { api } from '../api'
import type { FeedbackType, RecommendationItem } from '../types'

const feedbackLabels: Record<FeedbackType, string> = {
  relevant: 'Relevant',
  not_relevant: 'Not relevant',
  interested: 'Interested',
  already_played: 'Already played',
}

interface Props {
  item: RecommendationItem
  accessToken: string
  searchId?: string | null
  initiallyFavourite?: boolean
  onFavouriteChange?: (gameId: string, favourite: boolean) => void
}

export function RecommendationCard({
  item,
  accessToken,
  searchId,
  initiallyFavourite = false,
  onFavouriteChange,
}: Props) {
  const [isFavourite, setIsFavourite] = useState(initiallyFavourite)
  const [error, setError] = useState('')
  const [feedback, setFeedback] = useState<FeedbackType | null>(null)
  const reasons = item.personalisation_reasons ?? []
  const personalised = item.base_score != null && item.final_score != null
  const contextLabel = reasons.some(reason => reason.includes('favourites'))
    ? 'Because You Liked…'
    : reasons.some(reason => reason.includes('recent searches'))
      ? 'Based on Recent Searches'
      : reasons.length
        ? 'Based on Your Preferences'
        : null

  async function toggleFavourite() {
    const next = !isFavourite
    setIsFavourite(next)
    onFavouriteChange?.(item.game.id, next)
    setError('')
    try {
      if (next) await api.addFavourite(accessToken, item.game.id)
      else await api.removeFavourite(accessToken, item.game.id)
    } catch (caught) {
      setIsFavourite(!next)
      onFavouriteChange?.(item.game.id, !next)
      setError(caught instanceof Error ? caught.message : 'Could not update this favourite.')
    }
  }

  async function sendFeedback(value: FeedbackType) {
    setError('')
    try {
      await api.submitFeedback(accessToken, item.game.id, value, searchId)
      setFeedback(value)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not save feedback.')
    }
  }

  return <article className="activity-card">
    {contextLabel && <p className="personalisation-label">{contextLabel}</p>}
    <div className="card-heading"><div><h3>{item.game.title}</h3><p>{item.explanation}</p></div><button className="secondary compact" onClick={() => void toggleFavourite()}>{isFavourite ? 'Remove favourite' : 'Add favourite'}</button></div>
    <p className="meta">{item.game.genres.join(' · ')} · {Math.round(item.score * 100)}% match</p>
    {personalised && <details className="score-details"><summary>Why this score?</summary>
      <dl><dt>Base match</dt><dd>{item.base_score?.toFixed(1)}%</dd><dt>Personalisation</dt><dd>{item.personalisation_score && item.personalisation_score > 0 ? '+' : ''}{item.personalisation_score?.toFixed(1)} points</dd><dt>Final match</dt><dd>{item.final_score?.toFixed(1)}%</dd></dl>
      {reasons.length > 0 && <ul>{reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>}
    </details>}
    <div className="feedback-actions" aria-label={`Feedback for ${item.game.title}`}>
      {Object.entries(feedbackLabels).map(([value, label]) => <button className={feedback === value ? 'selected compact' : 'secondary compact'} key={value} onClick={() => void sendFeedback(value as FeedbackType)}>{label}</button>)}
    </div>
    {feedback && <p className="success" role="status">Feedback saved: {feedbackLabels[feedback]}.</p>}
    {error && <p className="error" role="alert">{error}</p>}
  </article>
}
