import type { ReactNode } from 'react'

interface LoadingStateProps {
  message: string
  fullPage?: boolean
}

export function LoadingState({ message, fullPage = false }: LoadingStateProps) {
  return <div className={`state-panel loading-state${fullPage ? ' full-page-state' : ''}`} role="status" aria-live="polite" aria-busy="true"><span className="spinner" aria-hidden="true" /><span>{message}</span></div>
}

export function ErrorState({ message, action }: { message: string; action?: ReactNode }) {
  return <div className="state-panel error-state" role="alert"><strong>Something went wrong</strong><p>{message}</p>{action && <div className="actions">{action}</div>}</div>
}

export function EmptyState({ title, message, action }: { title: string; message: string; action?: ReactNode }) {
  return <div className="card empty-state"><h2>{title}</h2><p>{message}</p>{action && <div className="actions centered-actions">{action}</div>}</div>
}
