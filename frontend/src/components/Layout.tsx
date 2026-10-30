import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth'

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const links = [
    { to: '/', label: 'Resumen', icon: '⌂' },
    { to: '/inventario', label: 'Inventario', icon: '▦' },
    { to: '/medicamentos', label: 'Medicamentos', icon: '＋' },
    { to: '/movimientos', label: 'Movimientos', icon: '↔' },
    { to: '/kardex', label: 'Kárdex', icon: '≡' },
    { to: '/alertas', label: 'Alertas', icon: '!' },
    { to: '/reportes', label: 'Reportes', icon: '📊' },
    ...(user?.role === 'ADMIN' ? [{ to: '/admin', label: 'Administración', icon: '⚙' }] : []),
  ]
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">✣</span><span>Farmacias<small>control operativo</small></span></div>
      <nav className="nav-list" aria-label="Navegación principal">{links.map(link => <NavLink key={link.to} to={link.to} end={link.to === '/'} className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}><span className="nav-icon">{link.icon}</span>{link.label}</NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="branch-chip"><span className="status-dot" />Sucursal principal</div><button className="user-mini" onClick={logout} title="Cerrar sesión"><span className="avatar">{user?.name.slice(0, 1).toUpperCase()}</span><span><strong>{user?.name}</strong><small>{user?.role === 'ADMIN' ? 'Administrador' : 'Empleado'}</small></span><span className="logout-icon">↗</span></button></div>
    </aside>
    <main className="main-content">{children}</main>
  </div>
}
