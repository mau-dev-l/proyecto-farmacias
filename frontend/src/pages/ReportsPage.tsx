import { useEffect, useMemo, useState } from 'react'
import { api, MOVEMENT_LABELS, type ExpiringLot, type InventoryItem, type InventoryReport, type KardexEntry, type WasteReport } from '../api'
import { useAuth } from '../auth'
import { Icons } from '../components/icons'
import { EmptyState, Field, Notice, PageHeader, StatusPill, Tabs } from '../components/Ui'

type ReportTab = 'inventario' | 'mermas' | 'proximos-vencer' | 'movimientos'

type ChartRow = { label: string; value: number; display: string }

const TAB_TITLES: Record<ReportTab, string> = {
  inventario: 'Inventario',
  mermas: 'Mermas y pérdidas',
  'proximos-vencer': 'Próximos a vencer',
  movimientos: 'Movimientos',
}

const CHART_TITLES: Record<ReportTab, string> = {
  inventario: 'Stock por medicamento',
  mermas: 'Pérdida por medicamento',
  'proximos-vencer': 'Valor en riesgo por medicamento',
  movimientos: 'Movimientos por día',
}

const CHART_HINTS: Record<ReportTab, string> = {
  inventario: 'Los 8 medicamentos con más unidades disponibles.',
  mermas: 'Los 8 medicamentos con mayor pérdida registrada.',
  'proximos-vencer': 'Los 8 lotes con mayor valor en riesgo.',
  movimientos: 'Cantidad de movimientos registrados por día.',
}

export function ReportsPage() {
  const { user } = useAuth()
  const [tab, setTab] = useState<ReportTab>('inventario')
  const [inventory, setInventory] = useState<InventoryReport>({ total_units: 0, total_value: '0', medicine_count: 0 })
  const [inventoryItems, setInventoryItems] = useState<InventoryItem[]>([])
  const [waste, setWaste] = useState<WasteReport>({ quantity: 0, total_value: '0', items: [] })
  const [expiring, setExpiring] = useState<ExpiringLot[]>([])
  const [movements, setMovements] = useState<KardexEntry[]>([])
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [days, setDays] = useState('30')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError('')
    const load = async () => {
      if (tab === 'inventario') {
        const [report, items] = await Promise.all([api.inventoryReport(), api.inventory()])
        setInventory(report)
        setInventoryItems(items)
      }
      if (tab === 'mermas') setWaste(await api.wasteReport(desde || undefined, hasta || undefined))
      if (tab === 'proximos-vencer') setExpiring(await api.expiringLots(Number(days)))
      if (tab === 'movimientos') setMovements(await api.movementsReport(desde || undefined, hasta || undefined))
    }
    load().catch(err => setError(err.message)).finally(() => setLoading(false))
  }, [tab, desde, hasta, days])

  const exportCurrent = async () => {
    setError('')
    try {
      if (tab === 'inventario') await api.exportReport('inventario')
      if (tab === 'mermas') await api.exportReport('mermas', { desde: desde || undefined, hasta: hasta || undefined })
      if (tab === 'proximos-vencer') await api.exportReport('proximos-vencer', { days: Number(days) })
      if (tab === 'movimientos') await api.exportReport('movimientos', { desde: desde || undefined, hasta: hasta || undefined })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo exportar')
    }
  }

  const chart = useMemo<ChartRow[]>(() => {
    if (tab === 'inventario') return [...inventoryItems].sort((a, b) => b.total_stock - a.total_stock).slice(0, 8)
      .map(item => ({ label: item.name, value: item.total_stock, display: `${item.total_stock} u.` }))
    if (tab === 'mermas') return [...waste.items].sort((a, b) => Number(b.total_value) - Number(a.total_value)).slice(0, 8)
      .map(item => ({ label: item.medicine_name, value: Number(item.total_value), display: `$ ${Number(item.total_value).toLocaleString('es-AR')}` }))
    if (tab === 'proximos-vencer') return [...expiring].sort((a, b) => Number(b.risk_value) - Number(a.risk_value)).slice(0, 8)
      .map(item => ({ label: `${item.medicine_name} · ${item.lot_number}`, value: Number(item.risk_value), display: `$ ${Number(item.risk_value).toLocaleString('es-AR')}` }))
    const buckets = new Map<string, number>()
    movements.forEach(movement => {
      const label = new Date(movement.created_at).toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' })
      buckets.set(label, (buckets.get(label) ?? 0) + 1)
    })
    return [...buckets.entries()].reverse().slice(-10).map(([label, count]) => ({ label, value: count, display: `${count} mov.` }))
  }, [tab, inventoryItems, waste, expiring, movements])

  const periodLabel = tab === 'inventario'
    ? 'Estado actual del inventario'
    : tab === 'proximos-vencer'
      ? `Lotes que vencen en los próximos ${days} días`
      : desde || hasta
        ? `Período: ${desde || 'inicio'} — ${hasta || 'hoy'}`
        : 'Histórico completo'

  return <>
    <div className="print-header">
      <div><span className="eyebrow">REPORTE DE SUCURSAL</span><h1>{TAB_TITLES[tab]}</h1><p>{periodLabel}</p></div>
      <div className="print-meta"><strong>{user?.name}</strong><span>Generado el {new Date().toLocaleString('es-AR')}</span></div>
    </div>

    <PageHeader
      eyebrow="ANÁLISIS"
      title="Reportes"
      description="Indicadores de inventario, pérdidas y movimientos. Exportables a CSV o PDF."
      action={<div className="header-actions">
        <button className="secondary-button" onClick={() => window.print()}><Icons.print className="btn-icon" aria-hidden="true" />Imprimir / PDF</button>
        <button className="primary-button" onClick={exportCurrent}><Icons.download className="btn-icon" aria-hidden="true" />Exportar CSV</button>
      </div>}
    />
    <Tabs
      value={tab}
      onChange={setTab}
      options={[
        { value: 'inventario', label: 'Inventario', icon: <Icons.units aria-hidden="true" /> },
        { value: 'mermas', label: 'Mermas y pérdidas', icon: <Icons.waste aria-hidden="true" /> },
        { value: 'proximos-vencer', label: 'Próximos a vencer', icon: <Icons.expiring aria-hidden="true" /> },
        { value: 'movimientos', label: 'Movimientos', icon: <Icons.movement aria-hidden="true" /> },
      ]}
    />
    {error && <Notice>{error}</Notice>}

    {(tab === 'mermas' || tab === 'movimientos') && <div className="toolbar">
      <Field label="Desde"><input type="date" value={desde} onChange={event => setDesde(event.target.value)} /></Field>
      <Field label="Hasta"><input type="date" value={hasta} onChange={event => setHasta(event.target.value)} /></Field>
    </div>}
    {tab === 'proximos-vencer' && <div className="toolbar">
      <Field label="Días de anticipación"><select value={days} onChange={event => setDays(event.target.value)}><option value="30">30 días</option><option value="60">60 días</option><option value="90">90 días</option><option value="180">180 días</option></select></Field>
    </div>}

    {loading ? <div className="panel loading-row">Calculando reporte…</div> : <>
      {tab === 'inventario' && <section className="metric-grid three">
        <div className="metric-card green"><span className="metric-icon"><Icons.units aria-hidden="true" /></span><span className="metric-label">Unidades en stock</span><strong>{inventory.total_units.toLocaleString('es-AR')}</strong><small>todos los lotes activos</small></div>
        <div className="metric-card blue"><span className="metric-icon"><Icons.value aria-hidden="true" /></span><span className="metric-label">Valor del inventario</span><strong>$ {Number(inventory.total_value).toLocaleString('es-AR')}</strong><small>costo de adquisición</small></div>
        <div className="metric-card amber"><span className="metric-icon"><Icons.medicineCount aria-hidden="true" /></span><span className="metric-label">Medicamentos</span><strong>{inventory.medicine_count}</strong><small>con stock disponible</small></div>
      </section>}

      {chart.length > 0 && <div className="panel table-panel report-chart">
        <div className="table-heading"><div><h2>{CHART_TITLES[tab]}</h2><span>{CHART_HINTS[tab]}</span></div></div>
        <HBarChart rows={chart} />
      </div>}

      {tab === 'mermas' && <div className="panel table-panel">
        <div className="table-heading"><div><h2>Pérdidas registradas como merma</h2><span>{waste.quantity.toLocaleString('es-AR')} unidades · $ {Number(waste.total_value).toLocaleString('es-AR')}</span></div></div>
        <p className="chart-note" style={{ marginTop: -8, marginBottom: 18 }}>Incluye mermas por vencimiento, rotura u otras causas registradas en el kárdex.</p>
        {waste.items.length === 0 ? <EmptyState title="Sin mermas" message="No hay pérdidas registradas en el rango elegido." /> : <div className="table-scroll"><table><thead><tr><th>Medicamento</th><th>Unidades perdidas</th><th>Pérdida económica</th></tr></thead><tbody>{waste.items.map(item => <tr key={item.medicine_name}><td><strong>{item.medicine_name}</strong></td><td>{item.quantity} u.</td><td>$ {Number(item.total_value).toLocaleString('es-AR')}</td></tr>)}</tbody></table></div>}
      </div>}

      {tab === 'proximos-vencer' && <div className="panel table-panel">
        <div className="table-heading"><div><h2>Lotes próximos a vencer</h2><span>{expiring.length} lotes en riesgo</span></div></div>
        {expiring.length === 0 ? <EmptyState title="Sin vencimientos próximos" message="No hay lotes dentro del umbral elegido." /> : <div className="table-scroll"><table><thead><tr><th>Medicamento</th><th>Lote</th><th>Caducidad</th><th>Días restantes</th><th>Cantidad</th><th>Valor en riesgo</th></tr></thead><tbody>{expiring.map(item => <tr key={item.lot_id}><td><strong>{item.medicine_name}</strong></td><td className="mono">{item.lot_number}</td><td>{item.expiration_date}</td><td><StatusPill tone={item.days_remaining <= 30 ? 'danger' : 'warning'}>{item.days_remaining} días</StatusPill></td><td>{item.quantity} u.</td><td>$ {Number(item.risk_value).toLocaleString('es-AR')}</td></tr>)}</tbody></table></div>}
      </div>}

      {tab === 'movimientos' && <div className="panel table-panel">
        <div className="table-heading"><div><h2>Movimientos del período</h2><span>{movements.length} registros</span></div></div>
        {movements.length === 0 ? <EmptyState title="Sin movimientos" message="No hay movimientos en el rango elegido." /> : <div className="table-scroll"><table><thead><tr><th>Fecha</th><th>Lote</th><th>Usuario</th><th>Tipo</th><th>Cantidad</th><th>Saldo</th></tr></thead><tbody>{movements.map(item => <tr key={item.id}><td>{new Date(item.created_at).toLocaleString('es-AR')}</td><td className="mono">{item.lot_number}</td><td>{item.user_name}</td><td>{MOVEMENT_LABELS[item.movement_type]}</td><td>{item.quantity} u.</td><td>{item.lot_balance} u.</td></tr>)}</tbody></table></div>}
      </div>}
    </>}
  </>
}

function HBarChart({ rows }: { rows: ChartRow[] }) {
  const max = Math.max(1, ...rows.map(row => row.value))
  return <div className="hbar-chart">{rows.map((row, index) => <div className="hbar-row" key={`${row.label}-${index}`}>
    <span className="hbar-label" title={row.label}>{row.label}</span>
    <span className="hbar-track"><span className="hbar-fill" style={{ width: `${Math.max(2, (row.value / max) * 100)}%` }} /></span>
    <span className="hbar-value">{row.display}</span>
  </div>)}</div>
}
