import { useEffect, useState } from 'react'
import { api, type ExpiringLot, type InventoryReport, type KardexEntry, type WasteReport } from '../api'
import { EmptyState, Field, Notice, PageHeader, StatusPill, Tabs } from '../components/Ui'

type ReportTab = 'inventario' | 'mermas' | 'proximos-vencer' | 'movimientos'

export function ReportsPage() {
  const [tab, setTab] = useState<ReportTab>('inventario')
  const [inventory, setInventory] = useState<InventoryReport>({ total_units: 0, total_value: '0', medicine_count: 0 })
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
      if (tab === 'inventario') setInventory(await api.inventoryReport())
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

  return <>
    <PageHeader eyebrow="ANÁLISIS" title="Reportes" description="Indicadores de inventario, pérdidas y movimientos, con exportación CSV." action={<button className="primary-button" onClick={exportCurrent}>Exportar CSV <span>↓</span></button>} />
    <Tabs
      value={tab}
      onChange={setTab}
      options={[
        { value: 'inventario', label: 'Inventario' },
        { value: 'mermas', label: 'Mermas' },
        { value: 'proximos-vencer', label: 'Próximos a vencer' },
        { value: 'movimientos', label: 'Movimientos' },
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
      {tab === 'inventario' && <section className="metric-grid">
        <div className="metric-card green"><span className="metric-mark" /><span className="metric-label">Unidades en stock</span><strong>{inventory.total_units.toLocaleString('es-AR')}</strong><small>todos los lotes activos</small></div>
        <div className="metric-card blue"><span className="metric-mark" /><span className="metric-label">Valor del inventario</span><strong>$ {Number(inventory.total_value).toLocaleString('es-AR')}</strong><small>costo de adquisición</small></div>
        <div className="metric-card amber"><span className="metric-mark" /><span className="metric-label">Medicamentos</span><strong>{inventory.medicine_count}</strong><small>con stock disponible</small></div>
      </section>}

      {tab === 'mermas' && <div className="panel table-panel">
        <div className="table-heading"><div><h2>Pérdidas por caducidad</h2><span>{waste.quantity} unidades · $ {Number(waste.total_value).toLocaleString('es-AR')}</span></div></div>
        {waste.items.length === 0 ? <EmptyState title="Sin mermas" message="No hay pérdidas registradas en el rango elegido." /> : <div className="table-scroll"><table><thead><tr><th>Medicamento</th><th>Unidades perdidas</th><th>Pérdida económica</th></tr></thead><tbody>{waste.items.map(item => <tr key={item.medicine_name}><td><strong>{item.medicine_name}</strong></td><td>{item.quantity} u.</td><td>$ {Number(item.total_value).toLocaleString('es-AR')}</td></tr>)}</tbody></table></div>}
      </div>}

      {tab === 'proximos-vencer' && <div className="panel table-panel">
        <div className="table-heading"><div><h2>Lotes próximos a vencer</h2><span>{expiring.length} lotes en riesgo</span></div></div>
        {expiring.length === 0 ? <EmptyState title="Sin vencimientos próximos" message="No hay lotes dentro del umbral elegido." /> : <div className="table-scroll"><table><thead><tr><th>Medicamento</th><th>Lote</th><th>Caducidad</th><th>Días restantes</th><th>Cantidad</th><th>Valor en riesgo</th></tr></thead><tbody>{expiring.map(item => <tr key={item.lot_id}><td><strong>{item.medicine_name}</strong></td><td className="mono">{item.lot_number}</td><td>{item.expiration_date}</td><td><StatusPill tone={item.days_remaining <= 30 ? 'danger' : 'warning'}>{item.days_remaining} días</StatusPill></td><td>{item.quantity} u.</td><td>$ {Number(item.risk_value).toLocaleString('es-AR')}</td></tr>)}</tbody></table></div>}
      </div>}

      {tab === 'movimientos' && <div className="panel table-panel">
        <div className="table-heading"><div><h2>Movimientos del período</h2><span>{movements.length} registros</span></div></div>
        {movements.length === 0 ? <EmptyState title="Sin movimientos" message="No hay movimientos en el rango elegido." /> : <div className="table-scroll"><table><thead><tr><th>Fecha</th><th>Lote</th><th>Usuario</th><th>Tipo</th><th>Cantidad</th><th>Saldo</th></tr></thead><tbody>{movements.map(item => <tr key={item.id}><td>{new Date(item.created_at).toLocaleString('es-AR')}</td><td className="mono">{item.lot_number}</td><td>{item.user_name}</td><td>{item.movement_type}</td><td>{item.quantity} u.</td><td>{item.lot_balance} u.</td></tr>)}</tbody></table></div>}
      </div>}
    </>}
  </>
}
