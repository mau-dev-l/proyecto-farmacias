export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description?: string; action?: React.ReactNode }) {
  return <header className="page-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</header>
}

export function StatusPill({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'neutral' | 'warning' | 'danger' | 'success' }) { return <span className={`status-pill ${tone}`}>{children}</span> }

export function EmptyState({ title, message }: { title: string; message: string }) { return <div className="empty-state"><span className="empty-icon">⌁</span><strong>{title}</strong><p>{message}</p></div> }
