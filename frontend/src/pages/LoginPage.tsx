import { FormEvent, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth'

export function LoginPage() {
  const { user, login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/" replace />
  async function submit(event: FormEvent) { event.preventDefault(); setError(''); setBusy(true); try { await login(email, password) } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo iniciar sesión') } finally { setBusy(false) } }
  return <div className="login-screen"><div className="login-art"><div className="login-art-inner"><span className="brand-mark large">✣</span><span className="eyebrow light">CONTROL DE FARMACIA</span><h1>Existencias claras.<br /><em>Decisiones seguras.</em></h1><p>Una vista precisa de cada lote, cada fecha y cada movimiento.</p><div className="art-stamp"><span>24</span><small>lotes bajo<br />seguimiento</small></div></div></div><main className="login-panel"><div className="login-card"><div className="mobile-brand"><span className="brand-mark">✣</span> Farmacias</div><span className="eyebrow">BIENVENIDO DE NUEVO</span><h2>Ingresá a tu cuenta</h2><p className="login-intro">Gestioná el inventario de tu sucursal con información al día.</p><form onSubmit={submit}><label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="nombre@farmacia.com" required /></label><label>Contraseña<input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required minLength={8} /></label>{error && <div className="form-error">{error}</div>}<button className="primary-button full" disabled={busy}>{busy ? 'Ingresando…' : 'Ingresar al panel'} <span>→</span></button></form><small className="login-footer">Acceso seguro para personal autorizado</small></div></main></div>
}
