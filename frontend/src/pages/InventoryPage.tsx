import { useEffect, useState } from 'react'
import { Fragment } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type InventoryItem } from '../api'
import { EmptyState, PageHeader, StatusPill } from '../components/Ui'

export function InventoryPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<InventoryItem[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    setError('')
    api.inventory(query).then(setItems).catch(err => setError(err.message)).finally(() => setLoading(false))
  }, [query])

  const exportCsv = async () => {
    try { await api.exportReport('inventario') } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo exportar') }
  }

  return <>
    <PageHeader eyebrow="CONTROL DE EXISTENCIAS" title="Inventario" description="Una lectura por medicamento de todo lo que está disponible." action={<><button className="secondary-button" onClick={exportCsv}>Exportar CSV ↓</button><button className="primary-button" onClick={() => navigate('/movimientos')}>+ Registrar entrada</button></>} />
    {error && <div className="notice danger">{error}</div>}
    <div className="toolbar"><label className="search-field"><span>⌕</span><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Buscar por nombre o código…" /></label><span className="toolbar-note">{items.length} medicamentos encontrados</span></div>
    <div className="panel table-panel">
      <div className="table-heading"><div><h2>Existencias actuales</h2><span>Stock total y desglose por lote</span></div></div>
      {loading ? <div className="loading-row">Cargando existencias…</div> : items.length === 0 ? <EmptyState title="No hay medicamentos" message="Probá con otra búsqueda o agregá un medicamento al catálogo." /> : <div className="table-scroll"><table><thead><tr><th>Medicamento</th><th>Código</th><th>Stock actual</th><th>Stock mínimo</th><th>Estado</th><th /></tr></thead><tbody>{items.map(item => {
        const low = item.total_stock <= item.minimum_stock
        const open = expanded === item.medicine_id
        return <Fragment key={item.medicine_id}>
          <tr key={item.medicine_id}>
            <td><strong>{item.name}</strong><small>{item.lots.length} lote(s) activos</small></td>
            <td className="mono">{item.barcode}</td>
            <td><strong>{item.total_stock}</strong> unidades</td>
            <td>{item.minimum_stock} unidades</td>
            <td><StatusPill tone={low ? 'danger' : 'success'}>{low ? 'Stock bajo' : 'En rango'}</StatusPill></td>
            <td><button className="row-menu" onClick={() => setExpanded(open ? null : item.medicine_id)}>{open ? '▴' : '▾'}</button></td>
          </tr>
          {open && item.lots.map(lot => <tr key={`${item.medicine_id}-${lot.id}`} className="detail-row"><td colSpan={6}><div className="inline-actions" style={{ justifyContent: 'space-between' }}><span className="mono">{lot.lot_number}</span><span>Vence {lot.expiration_date}</span><span>{lot.current_quantity} u. · {lot.status}</span></div></td></tr>)}
        </Fragment>
      })}</tbody></table></div>}
    </div>
  </>
}
