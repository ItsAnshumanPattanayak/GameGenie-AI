import { useEffect, useMemo, useRef, useState } from 'react'

import { mountTemplate } from './runtime'
import type { GameConfiguration } from './types'

interface Props {
  configuration: GameConfiguration
  mount?: typeof mountTemplate
}

export function GameHost({ configuration, mount = mountTemplate }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const [error, setError] = useState('')
  const configurationKey = useMemo(() => JSON.stringify(configuration), [configuration])

  useEffect(() => {
    if (!container.current) return
    setError('')
    try {
      return mount(container.current, configuration)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The game could not be started.')
    }
  }, [configurationKey, mount])

  return <section className="game-frame" aria-label={`${configuration.title} game`}>
    <div ref={container} className="phaser-mount" />
    {error && <p className="error" role="alert">{error}</p>}
    <p className="meta">Controls and restart instructions appear inside the game.</p>
  </section>
}
