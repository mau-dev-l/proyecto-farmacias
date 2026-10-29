import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, type User } from './api'

type AuthContext = { user: User | null; loading: boolean; login: (email: string, password: string) => Promise<void>; logout: () => void }
const Context = createContext<AuthContext | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    if (!localStorage.getItem('farmacias_token')) return setLoading(false)
    api.me().then(setUser).catch(() => localStorage.removeItem('farmacias_token')).finally(() => setLoading(false))
  }, [])
  const login = async (email: string, password: string) => {
    const result = await api.login(email, password)
    localStorage.setItem('farmacias_token', result.access_token)
    setUser(await api.me())
  }
  const logout = () => { localStorage.removeItem('farmacias_token'); setUser(null) }
  if (loading) return <div className="screen-loader">Cargando control operativo…</div>
  return <Context.Provider value={{ user, loading, login, logout }}>{children}</Context.Provider>
}

export function useAuth() {
  const context = useContext(Context)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
