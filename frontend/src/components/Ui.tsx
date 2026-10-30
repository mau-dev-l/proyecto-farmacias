export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description?: string; action?: React.ReactNode }) {
  return <header className="page-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</header>
}

export function StatusPill({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'neutral' | 'warning' | 'danger' | 'success' }) { return <span className={`status-pill ${tone}`}>{children}</span> }

export function EmptyState({ title, message }: { title: string; message: string }) { return <div className="empty-state"><span className="empty-icon">⌁</span><strong>{title}</strong><p>{message}</p></div> }

export function Notice({ tone = 'danger', children }: { tone?: 'danger' | 'success' | 'info'; children: React.ReactNode }) { return <div className={`notice ${tone}`}>{children}</div> }

export function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return <label className="field"><span>{label}</span>{children}{hint && <small>{hint}</small>}</label>
}

export function Modal({ open, title, description, onClose, children }: { open: boolean; title: string; description?: string; onClose: () => void; children: React.ReactNode }) {
  if (!open) return null
  return <div className="modal-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}>
    <section className="modal-card" role="dialog" aria-modal="true" aria-label={title}>
      <header className="modal-header"><div><h2>{title}</h2>{description && <p>{description}</p>}</div><button className="icon-button" onClick={onClose} aria-label="Cerrar">×</button></header>
      {children}
    </section>
  </div>
}

export function Tabs<T extends string>({ options, value, onChange }: { options: { value: T; label: string }[]; value: T; onChange: (value: T) => void }) {
  return <div className="tabs" role="tablist">{options.map(option => <button key={option.value} role="tab" aria-selected={value === option.value} className={value === option.value ? 'tab active' : 'tab'} onClick={() => onChange(option.value)}>{option.label}</button>)}</div>
}
