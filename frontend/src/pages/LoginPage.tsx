
import { FormEvent, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth'
import '../login.css'

export function LoginPage() {
  const { user, login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)

    try {
      await login(email, password)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'No se pudo iniciar sesión'
      )
    } finally {
      setBusy(false)
    }
  }

  if (user) return <Navigate to="/" replace />

  return (
    <div className="clinical-login">
      <section className="clinical-hero">
        <div className="clinical-brand">
          <span className="clinical-logo">✚</span>
          <div>
            <strong>FARMACIAS</strong>
            <small>Gestión inteligente</small>
          </div>
        </div>

        <div className="clinical-hero-content">
          <div className="clinical-symbol">✚</div>
          <span className="clinical-tag">
            SISTEMA DE GESTIÓN FARMACÉUTICA
          </span>
          <h1>
            Tu inventario,
            <br />
            <span>bajo control.</span>
          </h1>
          <p>
            Administra medicamentos, controla existencias
            y supervisa fechas de caducidad desde un
            solo lugar.
          </p>

          <div className="clinical-features">
            <div><span>✓</span> Control de inventarios</div>
            <div><span>✓</span> Seguimiento de caducidades</div>
            <div><span>✓</span> Gestión segura de medicamentos</div>
          </div>
        </div>

        <div className="clinical-hero-footer">
          Sistema de Inventarios y Control de Caducidades
        </div>
      </section>

      <main className="clinical-panel">
        <div className="clinical-card">
          <div className="clinical-mobile-logo">
            <span>✚</span> FARMACIAS
          </div>

          <div className="clinical-welcome-icon">✚</div>
          <span className="clinical-eyebrow">
            PORTAL DE ACCESO
          </span>

          <h2>Bienvenido de nuevo</h2>
          <p className="clinical-description">
            Ingresa tus credenciales para acceder
            al sistema de gestión farmacéutica.
          </p>

          <form onSubmit={submit}>
            <label htmlFor="clinical-email">
              Correo electrónico
            </label>
            <input
              id="clinical-email"
              type="email"
              autoComplete="username"
              placeholder="nombre@farmacia.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />

            <label htmlFor="clinical-password">
              Contraseña
            </label>
            <div className="clinical-password-wrap">
              <input
                id="clinical-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Ingresa tu contraseña"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={8}
              />
              <button
                type="button"
                className="clinical-show-password"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={
                  showPassword
                    ? 'Ocultar contraseña'
                    : 'Mostrar contraseña'
                }
              >
                {showPassword ? 'Ocultar' : 'Mostrar'}
              </button>
            </div>

            {error && (
              <div className="clinical-error" role="alert">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="clinical-submit"
              disabled={busy}
            >
              {busy ? 'Iniciando sesión...' : 'Iniciar sesión'}
              <span aria-hidden="true">→</span>
            </button>
          </form>

          <div className="clinical-security">
            <span>🔒</span>
            Acceso exclusivo para personal autorizado
          </div>
        </div>

        <p className="clinical-copyright">
          © {new Date().getFullYear()} Farmacias ·
          Sistema de gestión farmacéutica
        </p>
      </main>
    </div>
  )
}
