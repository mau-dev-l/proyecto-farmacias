const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export type User = {
  id: number
  branch_id: number
  name: string
  email: string
  role: 'ADMIN' | 'EMPLEADO'
  active: boolean
}

export type Medicine = {
  id: number
  barcode: string
  name: string
  active_ingredient?: string
  presentation?: string
  sale_price: string
  minimum_stock: number
  active: boolean
}

export type InventoryItem = {
  medicine_id: number
  name: string
  barcode: string
  minimum_stock: number
  total_stock: number
}

export type Alert = {
  id: number
  lot_id: number
  alert_type: 'PROXIMO_VENCER' | 'VENCIDO' | 'STOCK_MINIMO'
  threshold_days?: number
  read: boolean
  created_at: string
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('farmacias_token')
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? 'No se pudo completar la solicitud')
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

export const api = {
  login: (email: string, password: string) => request<{ access_token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request<User>('/auth/me'),
  dashboard: () => request<{ total_units: number; total_value: string; medicine_count: number; unread_alerts: number; expiring_lots: number }>('/reportes/dashboard'),
  inventory: (query = '') => request<InventoryItem[]>(`/inventario${query ? `?q=${encodeURIComponent(query)}` : ''}`),
  medicines: (query = '') => request<Medicine[]>(`/medicamentos${query ? `?q=${encodeURIComponent(query)}` : ''}`),
  alerts: () => request<Alert[]>('/alertas?leida=false'),
  markAlertRead: (id: number) => request<Alert>(`/alertas/${id}/leida`, { method: 'PATCH' }),
}
