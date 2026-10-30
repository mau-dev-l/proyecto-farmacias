const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export type User = {
  id: number
  branch_id: number
  name: string
  email: string
  role: 'ADMIN' | 'EMPLEADO'
  active: boolean
}

export type Branch = {
  id: number
  name: string
  address?: string | null
  active: boolean
}

export type Medicine = {
  id: number
  barcode: string
  name: string
  active_ingredient?: string | null
  presentation?: string | null
  sale_price: string
  minimum_stock: number
  active: boolean
}

export type InventoryLot = {
  id: number
  lot_number: string
  expiration_date: string
  current_quantity: number
  status: string
}

export type InventoryItem = {
  medicine_id: number
  name: string
  barcode: string
  minimum_stock: number
  total_stock: number
  lots: InventoryLot[]
}

export type Lot = {
  id: number
  medicine_id: number
  branch_id: number
  supplier_id?: number | null
  lot_number: string
  expiration_date: string
  current_quantity: number
  unit_cost: string
  status: string
}

export type Alert = {
  id: number
  lot_id: number
  alert_type: 'PROXIMO_VENCER' | 'VENCIDO' | 'STOCK_MINIMO'
  threshold_days?: number | null
  read: boolean
  created_at: string
  medicine_name: string
  lot_number: string
  expiration_date: string
  days_remaining: number
  quantity: number
}

export type AlertConfiguration = {
  branch_id: number
  lead_days: number
  thresholds: number[]
}

export type Movement = {
  id: number
  lot_id: number
  user_id: number
  movement_type: 'ENTRADA' | 'SALIDA_VENTA' | 'SALIDA_MERMA' | 'AJUSTE'
  quantity: number
  lot_balance: number
  unit_cost: string
  reason?: string | null
  created_at: string
}

export type KardexEntry = Movement & {
  lot_number: string
  user_name: string
}

export type SuggestedLot = {
  lot_id: number
  lot_number: string
  expiration_date: string
  available_quantity: number
  suggested_quantity: number
}

export type ExpiringLot = {
  lot_id: number
  medicine_name: string
  lot_number: string
  expiration_date: string
  days_remaining: number
  quantity: number
  risk_value: string
}

export type InventoryReport = {
  total_units: number
  total_value: string
  medicine_count: number
}

export type DashboardReport = InventoryReport & {
  unread_alerts: number
  expiring_lots: number
}

export type WasteItem = {
  medicine_name: string
  quantity: number
  total_value: string
}

export type WasteReport = {
  quantity: number
  total_value: string
  items: WasteItem[]
}

export type EntryPayload = {
  medicine_id: number
  lot_number: string
  expiration_date: string
  quantity: number
  unit_cost: string
  supplier_id?: number | null
  reason?: string | null
}

export type SalePayload = {
  medicine_id: number
  quantity: number
  movement_type: 'SALIDA_VENTA' | 'SALIDA_MERMA'
  lot_id?: number | null
  reason?: string | null
}

function queryString(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value))
  })
  const result = search.toString()
  return result ? `?${result}` : ''
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('farmacias_token')
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = Array.isArray(body.detail) ? body.detail.map((item: { msg: string }) => item.msg).join(', ') : body.detail
    throw new Error(detail ?? 'No se pudo completar la solicitud')
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

async function download(path: string, filename: string): Promise<void> {
  const token = localStorage.getItem('farmacias_token')
  const response = await fetch(`${API_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!response.ok) throw new Error('No se pudo exportar el reporte')
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export const api = {
  login: (email: string, password: string) => request<{ access_token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request<User>('/auth/me'),
  dashboard: () => request<DashboardReport>('/reportes/dashboard'),

  inventory: (query = '') => request<InventoryItem[]>(`/inventario${queryString({ q: query })}`),
  medicines: (query = '', page = 1, pageSize = 100) => request<Medicine[]>(`/medicamentos${queryString({ q: query, page, page_size: pageSize })}`),
  barcodeLookup: (barcode: string) => request<Medicine & { total_stock: number; lots: Lot[] }>(`/medicamentos/barcode/${encodeURIComponent(barcode)}`),
  createMedicine: (payload: Record<string, unknown>) => request<Medicine>('/medicamentos', { method: 'POST', body: JSON.stringify(payload) }),
  updateMedicine: (id: number, payload: Record<string, unknown>) => request<Medicine>(`/medicamentos/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteMedicine: (id: number) => request<void>(`/medicamentos/${id}`, { method: 'DELETE' }),
  lots: (medicineId: number) => request<Lot[]>(`/medicamentos/${medicineId}/lotes`),

  entry: (payload: EntryPayload) => request<Movement>('/movimientos/entrada', { method: 'POST', body: JSON.stringify(payload) }),
  pepsSuggestion: (medicineId: number, quantity: number) => request<SuggestedLot[]>(`/movimientos/peps-sugerido${queryString({ medicine_id: medicineId, quantity })}`),
  sale: (payload: SalePayload) => request<Movement[]>('/movimientos/salida', { method: 'POST', body: JSON.stringify(payload) }),
  kardex: (params: { medicine_id?: number; lot_id?: number; desde?: string; hasta?: string } = {}) => request<KardexEntry[]>(`/kardex${queryString(params)}`),

  alerts: (read?: boolean) => request<Alert[]>(`/alertas${queryString({ leida: read })}`),
  markAlertRead: (id: number) => request<Alert>(`/alertas/${id}/leida`, { method: 'PATCH' }),
  alertConfig: () => request<AlertConfiguration>('/alertas/configuracion'),
  setAlertConfig: (thresholds: number[]) => request<AlertConfiguration>('/alertas/configuracion', { method: 'PUT', body: JSON.stringify({ thresholds }) }),
  generateAlerts: () => request<{ created: number }>('/alertas/generar', { method: 'POST' }),

  expiringLots: (days = 30) => request<ExpiringLot[]>(`/reportes/proximos-vencer${queryString({ days })}`),
  wasteReport: (desde?: string, hasta?: string) => request<WasteReport>(`/reportes/mermas${queryString({ desde, hasta })}`),
  inventoryReport: () => request<InventoryReport>('/reportes/inventario'),
  movementsReport: (desde?: string, hasta?: string) => request<KardexEntry[]>(`/reportes/movimientos${queryString({ desde, hasta })}`),
  exportReport: (tipo: 'mermas' | 'proximos-vencer' | 'inventario' | 'movimientos', params: { desde?: string; hasta?: string; days?: number } = {}) =>
    download(`/reportes/exportar${queryString({ tipo, ...params })}`, `${tipo}.csv`),

  branches: () => request<Branch[]>('/sucursales'),
  createBranch: (payload: { name: string; address?: string }) => request<Branch>('/sucursales', { method: 'POST', body: JSON.stringify(payload) }),
  updateBranch: (id: number, payload: Partial<Branch>) => request<Branch>(`/sucursales/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  users: () => request<User[]>('/usuarios'),
  createUser: (payload: { branch_id: number; name: string; email: string; password: string; role: string }) => request<User>('/usuarios', { method: 'POST', body: JSON.stringify(payload) }),
  updateUser: (id: number, payload: Record<string, unknown>) => request<User>(`/usuarios/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
}
