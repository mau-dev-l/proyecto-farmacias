import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Alert, type InventoryItem, type InventoryReport, type KardexEntry, type WasteReport } from '../api'
import { useAuth } from '../auth'
import { Icons } from '../components/icons'
import { Notice, PageHeader } from '../components/Ui'

const DAY_MS = 86400000

/** Local calendar day as YYYY-MM-DD, so buckets match the user's timezone. */
function localDay(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

export function DashboardPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'ADMIN'
  const today = new Date().toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' }).toUpperCase()
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [kardex, setKardex] = useState<KardexEntry[]>([])
  const [report, setReport] = useState<InventoryReport | null>(null)
  const [waste, setWaste] = useState<WasteReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    const weekAgo = localDay(new Date(Date.now() - 6 * DAY_MS))
    const now = new Date()
    const monthStart = localDay(new Date(now.getFullYear(), now.getMonth(), 1))
    const failures: string[] = []

    const settle = <T,>(promise: Promise<T>, apply: (value: T) => void, label: string) =>
      promise.then(value => { if (active) apply(value) }).catch(() => { failures.push(label) })

    const load = async () => {
      await Promise.all([
        settle(api.inventory(), setInventory, 'inventario'),
        settle(api.alerts({ read: false }), setAlerts, 'alertas'),
        settle(api.kardex({ desde: weekAgo }), setKardex, 'movimientos'),
        ...(isAdmin ? [
          settle(api.inventoryReport(), setReport, 'valor del inventario'),
          settle(api.wasteReport(monthStart), setWaste, 'mermas del mes'),
        ] : []),
      ])
      if (!active) return
      setError(failures.length > 0 ? `No se pudieron cargar: ${failures.join(', ')}.` : '')
      setLoading(false)
    }
    load()
    return () => { active = false }
  }, [isAdmin])

  const totalUnits = inventory.reduce((total, item) => total + item.total_stock, 0)
  const inRange = inventory.filter(item => item.total_stock > item.minimum_stock).length
  const belowMinimum = inventory.length - inRange
  const ratio = inventory.length > 0 ? Math.round((inRange / inventory.length) * 100) : 0
  const expiring = alerts.filter(alert => alert.alert_type === 'PROXIMO_VENCER').length
  const expired = alerts.filter(alert => alert.alert_type === 'VENCIDO').length
  const lowStock = alerts.filter(alert => alert.alert_type === 'STOCK_MINIMO').length

  const week = useMemo(() => {
    const buckets = Array.from({ length: 7 }, (_, index) => {
      const date = new Date()
      date.setHours(0, 0, 0, 0)
      date.setDate(date.getDate() - (6 - index))
      return {
        key: localDay(date),
        label: date.toLocaleDateString('es-AR', { weekday: 'short' }).replace('.', ''),
        count: 0,
      }
    })
    kardex.forEach(movement => {
      const key = localDay(new Date(movement.created_at))
      const bucket = buckets.find(item => item.key === key)
      if (bucket) bucket.count += 1
    })
    return buckets
  }, [kardex])
  const peak = Math.max(1, ...week.map(item => item.count))
  const todayKey = localDay(new Date())

  return <>
    <PageHeader
      eyebrow={today}
      title="Buenos días, equipo."
      description="Este es el estado operativo de tu sucursal."
      action={<Link className="primary-button" to="/movimientos/entrada"><Icons.plus className="btn-icon" aria-hidden="true" />Registrar entrada</Link>}
    />
    {error && <Notice>{error}</Notice>}

    {loading ? <div className="panel loading-row">Cargando tablero…</div> : <>
      <section className="metric-grid">
        <Metric label="Unidades en stock" value={totalUnits.toLocaleString('es-AR')} detail="suma de todos los lotes activos" tone="green" />
        <Metric label="Medicamentos activos" value={inventory.length.toLocaleString('es-AR')} detail={`${inRange} con stock sobre el mínimo`} tone="blue" />
        <Metric label="Próximos a vencer" value={expiring} detail="alertas de vencimiento" tone="amber" />
        <Metric label="Alertas sin leer" value={alerts.length} detail="pendientes de revisión" tone="red" />
      </section>

      {isAdmin && <section className="metric-grid two">
        <Metric label="Valor del inventario" value={report ? `$ ${Number(report.total_value).toLocaleString('es-AR')}` : '—'} detail="costo de adquisición" tone="blue" />
        <Metric label="Mermas del mes" value={waste ? `${waste.quantity.toLocaleString('es-AR')} u.` : '—'} detail={waste ? `$ ${Number(waste.total_value).toLocaleString('es-AR')} de pérdida registrada` : 'sin datos del período'} tone="red" />
      </section>}

      <section className="dashboard-grid">
        <div className="panel large-panel">
          <div className="panel-heading"><div><span className="eyebrow">LECTURA RÁPIDA</span><h2>Salud del inventario</h2></div><span className="panel-date">Últimos 7 días</span></div>
          <div className="inventory-health">
            <div className="health-score">
              <div className="score-ring meter" style={{ background: `conic-gradient(var(--green) ${ratio}%, #d7e9dc 0)` }}>
                <span className="score-ring-inner"><strong>{ratio}%</strong><span>en rango</span></span>
              </div>
              <div>
                <strong>{belowMinimum === 0 ? 'Todo el catálogo en rango' : `${belowMinimum} medicamento(s) bajo el mínimo`}</strong>
                <p>{inRange} de {inventory.length} medicamentos tienen stock sobre su mínimo.</p>
              </div>
            </div>
            <div className="bar-chart">
              <div className="bars">{week.map(item => <i
                key={item.key}
                className={item.key === todayKey ? 'today' : item.count === 0 ? 'empty' : undefined}
                style={{ height: item.count === 0 ? '4%' : `${Math.max(8, Math.round((item.count / peak) * 100))}%` }}
                title={`${item.count} movimiento(s)`}
              />)}</div>
              <div className="bar-labels">{week.map(item => <span key={item.key}>{item.label}</span>)}</div>
            </div>
          </div>
          <p className="chart-note">Movimientos registrados por día en el kárdex de la sucursal.</p>
        </div>

        <div className="panel alert-panel">
          <div className="panel-heading"><div><span className="eyebrow">ATENCIÓN</span><h2>Alertas abiertas</h2></div><Link to="/alertas">Ver todas</Link></div>
          <Link className="alert-row" to="/alertas"><span className="alert-symbol red"><Icons.warning aria-hidden="true" /></span><div><strong>{expired} lotes vencidos</strong><p>Requieren retiro o merma</p></div><Icons.arrowRight className="arrow" aria-hidden="true" /></Link>
          <Link className="alert-row" to="/alertas"><span className="alert-symbol amber"><Icons.clock aria-hidden="true" /></span><div><strong>{expiring} lotes por vencer</strong><p>Dentro del umbral configurado</p></div><Icons.arrowRight className="arrow" aria-hidden="true" /></Link>
          <Link className="alert-row" to="/alertas"><span className="alert-symbol amber"><Icons.warning aria-hidden="true" /></span><div><strong>{lowStock} alertas de stock mínimo</strong><p>Reposición sugerida</p></div><Icons.arrowRight className="arrow" aria-hidden="true" /></Link>
        </div>
      </section>

      <section className="quick-section">
        <span className="eyebrow">ACCIONES FRECUENTES</span>
        <div className="quick-actions">
          <Link to="/inventario"><span className="quick-icon"><Icons.inventory aria-hidden="true" /></span><strong>Ver inventario</strong><small>Existencias por medicamento</small></Link>
          <Link to="/movimientos/salida"><span className="quick-icon"><Icons.sale aria-hidden="true" /></span><strong>Registrar salida</strong><small>Ventas y mermas por lote</small></Link>
          <Link to="/alertas"><span className="quick-icon"><Icons.clock aria-hidden="true" /></span><strong>Revisar vencimientos</strong><small>Priorizar lotes de riesgo</small></Link>
        </div>
      </section>
    </>}
  </>
}

function Metric({ label, value, detail, tone }: { label: string; value: React.ReactNode; detail: string; tone: string }) {
  const Icon = tone === 'green' ? Icons.units : tone === 'blue' ? Icons.value : tone === 'amber' ? Icons.expiring : Icons.alert
  return <div className={`metric-card ${tone}`}><span className="metric-icon"><Icon aria-hidden="true" /></span><span className="metric-label">{label}</span><strong>{value}</strong><small>{detail}</small></div>
}
