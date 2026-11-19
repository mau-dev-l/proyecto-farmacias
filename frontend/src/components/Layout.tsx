import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth'
import { BrandMark } from './BrandMark'
import { Icons } from './icons'

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const links = [
    { to: '/', label: 'Resumen', icon: Icons.dashboard },
    { to: '/inventario', label: 'Inventario', icon: Icons.inventory },
    { to: '/medicamentos', label: 'Medicamentos', icon: Icons.medicine },
    { to: '/movimientos', label: 'Movimientos', icon: Icons.movement },
    { to: '/kardex', label: 'Kárdex', icon: Icons.kardex },
    { to: '/alertas', label: 'Alertas', icon: Icons.alert },
    { to: '/reportes', label: 'Reportes', icon: Icons.report },
    { to: '/telegram', label: 'Telegram', icon: Icons.telegram },
    ...(user?.role === 'ADMIN' ? [{ to: '/admin', label: 'Administración', icon: Icons.admin }] : []),
  ]
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark"><BrandMark size={18} /></span><span>Farmacias<small>control operativo</small></span></div>
      <nav className="nav-list" aria-label="Navegación principal">{links.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}><span className="nav-icon"><Icon aria-hidden="true" /></span>{label}</NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="branch-chip"><span className="status-dot" />Sucursal principal</div><button className="user-mini" onClick={logout} title="Cerrar sesión"><span className="avatar">{user?.name.slice(0, 1).toUpperCase()}</span><span><strong>{user?.name}</strong><small>{user?.role === 'ADMIN' ? 'Administrador' : 'Empleado'}</small></span><span className="logout-icon" aria-hidden="true"><Icons.logout /></span></button></div>
    </aside>
    <main className="main-content">{children}</main>
  </div>
}
