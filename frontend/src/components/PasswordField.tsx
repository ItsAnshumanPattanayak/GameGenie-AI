import { useState } from 'react'
import type { InputHTMLAttributes } from 'react'

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string
}

export function PasswordField({ label, id, ...props }: Props) {
  const [visible, setVisible] = useState(false)
  return (
    <label htmlFor={id}>
      <span>{label}</span>
      <span className="password-row">
        <input id={id} type={visible ? 'text' : 'password'} {...props} />
        <button type="button" className="secondary compact" aria-label={`${visible ? 'Hide' : 'Show'} ${label.toLowerCase()}`} aria-pressed={visible} onClick={() => setVisible((value) => !value)}>
          {visible ? 'Hide' : 'Show'}
        </button>
      </span>
    </label>
  )
}
