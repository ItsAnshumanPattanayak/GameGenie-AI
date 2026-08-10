import { useEffect, useMemo, useRef, useState } from 'react'

import { mountTemplate } from './runtime'
import { templateLabel } from './types'
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

  const instructions = configuration.template === 'space_shooter'
    ? 'Move with the arrow keys, fire with Space, and press R or click after game over to restart.'
    : configuration.template === 'endless_runner'
      ? 'Jump with Space or the up arrow, and press R or click after game over to restart.'
      : 'Move with the arrow keys, reach the exit before time expires, and press R or click after the game ends to restart.'

  return <section className="game-frame" aria-label={`${configuration.title}, ${templateLabel(configuration.template)}`}>
    <div ref={container} className="phaser-mount" aria-label={`${templateLabel(configuration.template)} canvas`} />
    {error && <p className="error" role="alert">{error}</p>}
    <p className="meta game-instructions">{instructions}</p>
  </section>
}
