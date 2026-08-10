import { useEffect, useState } from 'react'

import { api, errorMessage } from '../api'
import { useAuth } from '../auth/AuthContext'
import { ErrorState, LoadingState } from '../components/PageState'
import { TAXONOMY } from '../taxonomy'
import type { PreferenceInput, UserPreferences } from '../types'

const EMPTY: PreferenceInput = {
  preferred_genres: [], preferred_platforms: [], preferred_modes: [], preferred_moods: [],
  preferred_difficulty: null, price_preference: null, hardware_level: null,
}
type ListField = 'preferred_genres' | 'preferred_platforms' | 'preferred_modes' | 'preferred_moods'

function toInput(preferences: UserPreferences): PreferenceInput {
  return {
    preferred_genres: preferences.preferred_genres,
    preferred_platforms: preferences.preferred_platforms,
    preferred_modes: preferences.preferred_modes,
    preferred_moods: preferences.preferred_moods,
    preferred_difficulty: preferences.preferred_difficulty,
    price_preference: preferences.price_preference,
    hardware_level: preferences.hardware_level,
  }
}

export function PreferencesPage() {
  const { accessToken } = useAuth()
  const [values, setValues] = useState<PreferenceInput>(EMPTY)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loadFailed, setLoadFailed] = useState(false)

  useEffect(() => {
    if (!accessToken) return
    api.preferences(accessToken)
      .then(({ preferences }) => setValues(toInput(preferences)))
      .catch((reason: unknown) => { setLoadFailed(true); setError(errorMessage(reason, 'Could not load preferences.')) })
      .finally(() => setLoading(false))
  }, [accessToken])

  function toggle(field: ListField, option: string) {
    setValues((current) => ({
      ...current,
      [field]: current[field].includes(option)
        ? current[field].filter((value) => value !== option)
        : [...current[field], option],
    }))
  }

  async function save(event: React.FormEvent) {
    event.preventDefault()
    if (!accessToken) return
    setSaving(true); setError(''); setMessage('')
    try {
      const response = await api.updatePreferences(accessToken, values)
      setValues(toInput(response.preferences))
      setMessage('Preferences saved.')
    } catch (reason) {
      setError(errorMessage(reason, 'Could not save preferences.'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingState message="Loading preferences…" />
  if (loadFailed) return <section><p className="eyebrow">Recommendation controls</p><h1>Your preferences</h1><ErrorState message={error} /></section>
  return (
    <form className="card page-card preferences" onSubmit={save}>
      <p className="eyebrow">Recommendation controls</p>
      <h1>Your preferences</h1>
      <PreferenceGroup title="Genres" options={TAXONOMY.genres} selected={values.preferred_genres} onToggle={(value) => toggle('preferred_genres', value)} />
      <PreferenceGroup title="Platforms" options={TAXONOMY.platforms} selected={values.preferred_platforms} onToggle={(value) => toggle('preferred_platforms', value)} />
      <PreferenceGroup title="Modes" options={TAXONOMY.modes} selected={values.preferred_modes} onToggle={(value) => toggle('preferred_modes', value)} />
      <PreferenceGroup title="Moods" options={TAXONOMY.moods} selected={values.preferred_moods} onToggle={(value) => toggle('preferred_moods', value)} />
      <SelectPreference label="Difficulty" value={values.preferred_difficulty} options={TAXONOMY.difficulty} onChange={(value) => setValues({ ...values, preferred_difficulty: value })} />
      <SelectPreference label="Price preference" value={values.price_preference} options={TAXONOMY.price} onChange={(value) => setValues({ ...values, price_preference: value })} />
      <SelectPreference label="Hardware level" value={values.hardware_level} options={TAXONOMY.hardware} onChange={(value) => setValues({ ...values, hardware_level: value })} />
      {error && <ErrorState message={error} />}
      {message && <p className="success" role="status">{message}</p>}
      <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save preferences'}</button>
    </form>
  )
}

function PreferenceGroup({ title, options, selected, onToggle }: { title: string; options: readonly string[]; selected: string[]; onToggle(value: string): void }) {
  return <fieldset><legend>{title}</legend><div className="choice-grid">{options.map((option) => (
    <label className="choice" key={option}><input type="checkbox" checked={selected.includes(option)} onChange={() => onToggle(option)} />{option}</label>
  ))}</div></fieldset>
}

function SelectPreference({ label, value, options, onChange }: { label: string; value: string | null; options: readonly string[]; onChange(value: string | null): void }) {
  const id = label.toLowerCase().replaceAll(' ', '-')
  return <label htmlFor={id}><span>{label}</span><select id={id} value={value ?? ''} onChange={(event) => onChange(event.target.value || null)}><option value="">No preference</option>{options.map((option) => <option key={option}>{option}</option>)}</select></label>
}
