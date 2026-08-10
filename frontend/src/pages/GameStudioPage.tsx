import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { api } from '../api'
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
  const selectedGameId = searchParams.get('game')
  const [prompt, setPrompt] = useState<string>(examples[0][1])
  const [configuration, setConfiguration] = useState<GameConfiguration | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function generate() {
    if (!prompt.trim()) { setError('Describe the game you want to generate.'); return }
    setLoading(true); setError(''); setWarnings([])
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

  return <section><p className="eyebrow">Multi-template studio</p><h1>Generate a playable game</h1>
    <p>Choose one of the three supported templates or describe a variation. Generated settings directly control the scene.</p>
    <div className="actions template-examples">{examples.map(([label, value]) => <button className="secondary" key={label} onClick={() => setPrompt(value)}>{label}</button>)}</div>
    <label className="generator-prompt">Game prompt<textarea value={prompt} onChange={event => setPrompt(event.target.value)} rows={4} /></label>
    <button disabled={loading} onClick={() => void generate()}>{loading ? 'Generating…' : 'Generate and play'}</button>
    {error && <p className="error" role="alert">{error}</p>}
    {warnings.length > 0 && <div className="warning" role="status"><strong>Adaptation notes</strong><ul>{warnings.map(warning => <li key={warning}>{warning}</li>)}</ul></div>}
    {configuration && <><div className="configuration-summary card"><h2>{configuration.title}</h2><p><strong>Template:</strong> {configuration.template.replaceAll('_', ' ')} · <strong>Theme:</strong> {configuration.theme} · <strong>Difficulty:</strong> {configuration.difficulty}</p><p className="meta">Active settings: {getTemplateDefinition(configuration.template).supportedSettings.join(', ')}</p></div><GameHost configuration={configuration} /></>}
  </section>
}
