import { cloneElement, isValidElement, useEffect, useId, useRef } from 'react'
import type { ButtonHTMLAttributes, HTMLAttributes, ReactElement, ReactNode } from 'react'

export function Panel({ children, className = '', ...props }: HTMLAttributes<HTMLElement> & { children: ReactNode }) {
  return <section className={`panel ${className}`.trim()} {...props}>{children}</section>
}

export function Card({ children, className = '', ...props }: HTMLAttributes<HTMLElement> & { children: ReactNode }) {
  return <article className={`card ${className}`.trim()} {...props}>{children}</article>
}

export function Button({ className = '', type = 'button', ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type={type} className={className} {...props} />
}

export function StatusPill({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'warning' | 'danger' }) {
  return <span className="status-pill" data-tone={tone}>{children}</span>
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="empty-state">{children}</p>
}

export function Field({ id, label, hint, error, children }: {
  id: string
  label: ReactNode
  hint?: ReactNode
  error?: ReactNode
  children: ReactNode
}) {
  const hintId = hint ? `${id}-hint` : undefined
  const errorId = error ? `${id}-error` : undefined
  const controlProps = { id, 'aria-describedby': [hintId, errorId].filter(Boolean).join(' ') || undefined, 'aria-invalid': error ? true : undefined }
  const control = isValidElement(children)
    ? cloneElement(children as ReactElement<{ id?: string; 'aria-describedby'?: string; 'aria-invalid'?: boolean }>, controlProps)
    : children
  return <div className="field-group"><label htmlFor={id}>{label}</label>{control}
    {hint && <small className="field-hint" id={hintId}>{hint}</small>}
    {error && <small className="error-state" id={errorId}>{error}</small>}
  </div>
}

export function Dialog({ open, title, closeLabel, onClose, children }: {
  open: boolean
  title: string
  closeLabel: string
  onClose: () => void
  children: ReactNode
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (open && !element.open) element.showModal()
    if (!open && element.open) element.close()
  }, [open])
  return <dialog ref={dialog} aria-labelledby={titleId} onCancel={event => { event.preventDefault(); onClose() }}>
    <div className="dialog-content"><h2 id={titleId}>{title}</h2>{children}
      <Button className="secondary" onClick={onClose}>{closeLabel}</Button></div>
  </dialog>
}

export function PageHeading({ title, description }: { title: ReactNode; description?: ReactNode }) {
  return <div className="page-heading"><div><h2>{title}</h2>{description && <p>{description}</p>}</div></div>
}

export function JourneyNav({ items, active, onChange, label }: {
  items: { id: string; label: string }[]
  active: string
  onChange: (id: string) => void
  label: string
}) {
  return <nav className="app-nav" aria-label={label}>
    {items.map(item => <Button key={item.id} aria-current={item.id === active ? 'page' : undefined}
      onClick={() => onChange(item.id)}>{item.label}</Button>)}
  </nav>
}

export function TimezoneNote({ label, timezone }: { label: string; timezone: string }) {
  return <p className="timezone">{label}: <b>{timezone}</b></p>
}
