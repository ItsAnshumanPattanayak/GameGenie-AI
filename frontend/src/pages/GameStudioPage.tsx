import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { api } from '../api'
import { useAuth } from '../auth/AuthContext'
import { GameHost } from '../games/GameHost'
import { getTemplateDefinition } from '../games/registry'
import type { GameConfiguration } from '../games/types'

const examples = [
  ['Space Shooter', 'hard cyberpunk space shooter with fast enemies and increasing difficulty'],
  ['Endless Runner', 'neon endless runner with high jumps, many obstacles, and gets faster'],
  ['Maze Escape', 'hard jungle maze escape with a short timer and many obstacles'],
] as const

export function GameStudioPage() {
  const [searchParams] = useSearchParams()
  const { accessToken } = useAuth()
  const selectedGameId = searchParams.get('game')
  const requestedSavedId = searchParams.get('saved')
  const [prompt, setPrompt] = useState<string>(examples[0][1])
  const [configuration, setConfiguration] = useState<GameConfiguration | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [persistedId, setPersistedId] = useState(requestedSavedId ?? '')
  const [saveMessage, setSaveMessage] = useState('')
  const [saving, setSaving] = useState(false)
  const [loadingSaved, setLoadingSaved] = useState(Boolean(requestedSavedId))

  useEffect(() => {
    if (!requestedSavedId || !accessToken) { setLoadingSaved(false); return }
    let active = true
    api.generatedGame(accessToken, requestedSavedId)
      .then(result => {
        if (!active) return
        setPrompt(result.item.prompt)
        setConfiguration(result.item.configuration)
        setPersistedId(result.item.id)
      })
      .catch(caught => { if (active) setError(caught instanceof Error ? caught.message : 'The saved game could not be loaded.') })
      .finally(() => { if (active) setLoadingSaved(false) })
    return () => { active = false }
  }, [accessToken, requestedSavedId])

  async function generate() {
    if (!prompt.trim()) { setError('Describe the game you want to generate.'); return }
    setLoading(true); setError(''); setWarnings([]); setSaveMessage('')
    try {
      const result = await api.generateGame(prompt, selectedGameId)
      setWarnings(result.warnings.map(warning => warning.message))
      if (!result.success || !result.configuration) {
        setConfiguration(null)
        setError(result.selection.reason)
        return
      }
      setConfiguration(result.configuration)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The game configuration could not be generated.')
    } finally {
      setLoading(false)
    }
  }

  async function save() {
    if (!configuration || !accessToken) return
    setSaving(true); setError(''); setSaveMessage('')
    const payload = {
      title: configuration.title,
      prompt,
      template_type: configuration.template,
      configuration,
      config_version: '1.1',
    }
    try {
      const wasPersisted = Boolean(persistedId)
      const result = persistedId
        ? await api.updateGeneratedGame(accessToken, persistedId, payload)
        : await api.createGeneratedGame(accessToken, payload)
      setPersistedId(result.item.id)
      setConfiguration(result.item.configuration)
      setSaveMessage(wasPersisted ? 'Saved game updated.' : 'Game saved to My Games.')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The generated game could not be saved.')
    } finally {
      setSaving(false)
    }
  }

  if (loadingSaved) return <p role="status">Loading saved settings…</p>

  return <section><p className="eyebrow">Multi-template studio</p><h1>Generate a playable game</h1>
    <p>Choose one of the three supported templates or describe a variation. Generated settings directly control the scene.</p>
    <div className="actions template-examples">{examples.map(([label, value]) => <button className="secondary" key={label} onClick={() => setPrompt(value)}>{label}</button>)}</div>
    <label className="generator-prompt">Game prompt<textarea value={prompt} onChange={event => setPrompt(event.target.value)} rows={4} /></label>
    <button disabled={loading} onClick={() => void generate()}>{loading ? 'Generating…' : 'Generate and play'}</button>
    {error && <p className="error" role="alert">{error}</p>}
    {warnings.length > 0 && <div className="warning" role="status"><strong>Adaptation notes</strong><ul>{warnings.map(warning => <li key={warning}>{warning}</li>)}</ul></div>}
    {saveMessage && <p className="success" role="status">{saveMessage}</p>}
    {configuration && <><div className="configuration-summary card"><h2>{configuration.title}</h2><p><strong>Template:</strong> {configuration.template.replaceAll('_', ' ')} · <strong>Theme:</strong> {configuration.theme} · <strong>Difficulty:</strong> {configuration.difficulty}</p><p className="meta">Active settings: {getTemplateDefinition(configuration.template).supportedSettings.join(', ')}</p><div className="actions"><button disabled={saving} onClick={() => void save()}>{saving ? 'Saving…' : persistedId ? 'Update saved game' : 'Save game'}</button>{persistedId && <Link className="button-link secondary" to={`/play/saved/${persistedId}`}>Open saved game</Link>}</div></div><GameHost configuration={configuration} /></>}
  </section>
}
