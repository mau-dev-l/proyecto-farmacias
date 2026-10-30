import { useEffect, useMemo, useState } from 'react'
import { api, type KardexEntry, type Lot, type Medicine } from '../api'
import { EmptyState, Field, Notice, PageHeader, StatusPill } from '../components/Ui'

const typeLabels: Record<KardexEntry['movement_type'], string> = {
  ENTRADA: 'Entrada',
  SALIDA_VENTA: 'Venta',
  SALIDA_MERMA: 'Merma',
  AJUSTE: 'Ajuste',
}

export function KardexPage() {
  const [medicines, setMedicines] = useState<Medicine[]>([])
  const [medicineId, setMedicineId] = useState('')
  const [lots, setLots] = useState<Lot[]>([])
  const [lotId, setLotId] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [entries, setEntries] = useState<KardexEntry[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const selected = useMemo(() => medicines.find(item => item.id === Number(medicineId)), [medicines, medicineId])

  useEffect(() => {
    api.medicines('', 1, 100).then(setMedicines).catch(err => setError(err.message))
  }, [])

  useEffect(() => {
    setLotId('')
    if (!medicineId) return setLots([])
    api.lots(Number(medicineId)).then(setLots).catch(() => setLots([]))
  }, [medicineId])

  useEffect(() => {
    setLoading(true)
    setError('')
    api.kardex({
      medicine_id: medicineId ? Number(medicineId) : undefined,
      lot_id: lotId ? Number(lotId) : undefined,
      desde: desde || undefined,
      hasta: hasta || undefined,
    })
      .then(setEntries)
      .catch(err => { setEntries([]); setError(err.message) })
      .finally(() => setLoading(false))
  }, [medicineId, lotId, desde, hasta])

  return <>
    <PageHeader eyebrow="TRAZABILIDAD" title="Kárdex" description="Cada movimiento queda asociado a un lote, un usuario y un saldo." />
    {error && <Notice>{error}</Notice>}
    <div className="toolbar">
      <Field label="Medicamento">
        <select value={medicineId} onChange={event => setMedicineId(event.target.value)}>
          <option value="">Todos</option>
          {medicines.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </Field>
      <Field label="Lote">
        <select value={lotId} onChange={event => setLotId(event.target.value)} disabled={!medicineId}>
          <option value="">Todos</option>
          {lots.map(lot => <option key={lot.id} value={lot.id}>{lot.lot_number}</option>)}
        </select>
      </Field>
      <Field label="Desde">
        <input type="date" value={desde} onChange={event => setDesde(event.target.value)} />
      </Field>
      <Field label="Hasta">
        <input type="date" value={hasta} onChange={event => setHasta(event.target.value)} />
      </Field>
    </div>
    <div className="panel table-panel">
      <div className="table-heading"><div><h2>{selected ? `Movimientos de ${selected.name}` : 'Movimientos registrados'}</h2><span>{entries.length} movimientos</span></div></div>
      {loading ? <div className="loading-row">Cargando kárdex…</div> : entries.length === 0 ? <EmptyState title="Sin movimientos" message="No hay movimientos para los filtros elegidos." /> : <div className="table-scroll"><table>
        <thead><tr><th>Fecha</th><th>Lote</th><th>Usuario</th><th>Tipo</th><th>Cantidad</th><th>Saldo del lote</th><th>Costo</th><th>Motivo</th></tr></thead>
        <tbody>{entries.map(entry => <tr key={entry.id}>
          <td>{new Date(entry.created_at).toLocaleString('es-AR')}</td>
          <td className="mono">{entry.lot_number}</td>
          <td>{entry.user_name}</td>
          <td><StatusPill tone={entry.movement_type === 'ENTRADA' ? 'success' : entry.movement_type === 'SALIDA_MERMA' ? 'danger' : 'warning'}>{typeLabels[entry.movement_type]}</StatusPill></td>
          <td><strong>{entry.quantity}</strong> u.</td>
          <td>{entry.lot_balance} u.</td>
          <td>$ {Number(entry.unit_cost).toLocaleString('es-AR')}</td>
          <td>{entry.reason || '—'}</td>
        </tr>)}</tbody>
      </table></div>}
    </div>
  </>
}
