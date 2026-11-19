import { useEffect, useMemo, useState } from 'react'
import { api, type Lot, type Medicine, type SuggestedLot } from '../api'
import { Icons } from './icons'
import { EmptyState, Field, Notice, StatusPill, Tabs } from './Ui'

type SaleType = 'SALIDA_VENTA' | 'SALIDA_MERMA'

const today = () => new Date().toISOString().slice(0, 10)
const inDays = (days: number) => new Date(Date.now() + days * 86400000).toISOString().slice(0, 10)

/**
 * Shared movement form.
 *
 * `kind="ENTRADA"` renders the entry fields (create or extend a lot) and
 * `kind="SALIDA"` renders the exit fields plus a sale/waste switch. Each page
 * owns its header and description.
 */
export function MovementForm({ kind }: { kind: 'ENTRADA' | 'SALIDA' }) {
  const isEntry = kind === 'ENTRADA'
  const [saleType, setSaleType] = useState<SaleType>('SALIDA_VENTA')
  const [medicines, setMedicines] = useState<Medicine[]>([])
  const [medicineId, setMedicineId] = useState('')
  const [lots, setLots] = useState<Lot[]>([])
  const [suggestion, setSuggestion] = useState<SuggestedLot[]>([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [saving, setSaving] = useState(false)

  const [lotNumber, setLotNumber] = useState('')
  const [expirationDate, setExpirationDate] = useState(inDays(180))
  const [quantity, setQuantity] = useState('1')
  const [unitCost, setUnitCost] = useState('')
  const [lotId, setLotId] = useState('')
  const [reason, setReason] = useState('')

  const selected = useMemo(() => medicines.find(item => item.id === Number(medicineId)), [medicines, medicineId])
  const sortedLots = useMemo(() => [...lots].sort((a, b) => a.expiration_date.localeCompare(b.expiration_date)), [lots])

  useEffect(() => {
    api.medicines('', 1, 100).then(setMedicines).catch(err => setError(err.message))
  }, [])

  useEffect(() => {
    setSuggestion([])
    setLotId('')
    if (!medicineId) {
      setLots([])
      return
    }
    api.lots(Number(medicineId)).then(setLots).catch(() => setLots([]))
  }, [medicineId])

  const reset = () => {
    setQuantity('1')
    setReason('')
    setSuggestion([])
    setLotId('')
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    setSaving(true)
    try {
      if (!medicineId) throw new Error('Seleccioná un medicamento')
      if (isEntry) {
        await api.entry({
          medicine_id: Number(medicineId),
          lot_number: lotNumber,
          expiration_date: expirationDate,
          quantity: Number(quantity),
          unit_cost: unitCost,
          reason: reason || null,
        })
        setSuccess(`Entrada registrada para ${selected?.name}. El lote quedó actualizado.`)
        setLotNumber('')
        setUnitCost('')
        reset()
      } else {
        const movements = await api.sale({
          medicine_id: Number(medicineId),
          quantity: Number(quantity),
          movement_type: saleType,
          lot_id: lotId ? Number(lotId) : null,
          reason: reason || null,
        })
        setSuccess(`${saleType === 'SALIDA_MERMA' ? 'Merma' : 'Venta'} registrada en ${movements.length} lote(s).`)
        reset()
      }
      setLots(await api.lots(Number(medicineId)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar el movimiento')
    } finally {
      setSaving(false)
    }
  }

  const calculateSuggestion = async () => {
    setError('')
    setSuggestion([])
    try {
      if (!medicineId) throw new Error('Seleccioná un medicamento')
      setSuggestion(await api.pepsSuggestion(Number(medicineId), Number(quantity)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo calcular la sugerencia')
    }
  }

  const manualLot = lots.find(lot => lot.id === Number(lotId))
  const needsReason = !isEntry && Boolean(lotId) && suggestion.length > 0 && suggestion[0].lot_id !== Number(lotId)
  const SubmitIcon = isEntry ? Icons.entry : saleType === 'SALIDA_MERMA' ? Icons.waste : Icons.sale
  const submitLabel = isEntry ? 'Registrar entrada' : saleType === 'SALIDA_MERMA' ? 'Registrar merma' : 'Registrar venta'

  return <>
    {error && <Notice>{error}</Notice>}
    {success && <Notice tone="success">{success}</Notice>}

    <div className="split-panel">
      <form className="panel table-panel" onSubmit={submit}>
        <div className="table-heading"><div><h2>{isEntry ? 'Datos de la entrada' : 'Datos de la salida'}</h2><span>{isEntry ? 'Crea un lote nuevo o suma unidades al existente' : 'El stock se descuenta por FEFO: primero vence, primero sale'}</span></div></div>
        {!isEntry && <Tabs
          value={saleType}
          onChange={value => { setSaleType(value); setError(''); setSuccess(''); reset() }}
          options={[
            { value: 'SALIDA_VENTA', label: 'Venta', icon: <Icons.sale aria-hidden="true" /> },
            { value: 'SALIDA_MERMA', label: 'Merma', icon: <Icons.waste aria-hidden="true" /> },
          ]}
        />}
        <div className="form-grid">
          <Field label="Medicamento">
            <select value={medicineId} onChange={event => setMedicineId(event.target.value)} required>
              <option value="">Seleccionar…</option>
              {medicines.map(item => <option key={item.id} value={item.id}>{item.name} · {item.barcode}</option>)}
            </select>
          </Field>
          <Field label="Cantidad">
            <input type="number" min="1" value={quantity} onChange={event => setQuantity(event.target.value)} required />
          </Field>

          {isEntry ? <>
            <Field label="Número de lote">
              <input value={lotNumber} onChange={event => setLotNumber(event.target.value)} placeholder="Ej. IBU-2601" required maxLength={50} />
            </Field>
            <Field label="Fecha de caducidad">
              <input type="date" min={today()} value={expirationDate} onChange={event => setExpirationDate(event.target.value)} required />
            </Field>
            <Field label="Costo unitario">
              <input type="number" min="0" step="0.01" value={unitCost} onChange={event => setUnitCost(event.target.value)} placeholder="0.00" required />
            </Field>
          </> : <Field label="Lote" hint="Dejalo vacío para que el sistema aplique FEFO automáticamente.">
            <select value={lotId} onChange={event => setLotId(event.target.value)}>
              <option value="">FEFO automático</option>
              {sortedLots.filter(lot => lot.current_quantity > 0).map(lot => <option key={lot.id} value={lot.id}>{lot.lot_number} · vence {lot.expiration_date} · {lot.current_quantity} u.</option>)}
            </select>
          </Field>}

          <Field label="Motivo" hint={needsReason ? 'Obligatorio al elegir un lote distinto al sugerido.' : 'Opcional, queda en el kárdex.'}>
            <input value={reason} onChange={event => setReason(event.target.value)} placeholder={saleType === 'SALIDA_MERMA' ? 'Ej. Lote vencido' : 'Ej. Pedido especial'} maxLength={255} required={needsReason} />
          </Field>

          {!isEntry && <div className="span-2 inline-actions">
            <button type="button" className="secondary-button" onClick={calculateSuggestion}><Icons.calculate className="btn-icon" aria-hidden="true" />Sugerir lotes</button>
            <span className="toolbar-note">Ordena por fecha de caducidad más próxima.</span>
          </div>}

          <div className="span-2 form-actions">
            <button className="primary-button" disabled={saving}><SubmitIcon className="btn-icon" aria-hidden="true" />{saving ? 'Guardando…' : submitLabel}</button>
          </div>
        </div>
      </form>

      <aside className="panel table-panel">
        <div className="table-heading"><div><h2>{selected ? selected.name : 'Sin medicamento'}</h2><span>{selected ? `Stock mínimo ${selected.minimum_stock} u.` : 'Elegí un medicamento para ver sus lotes'}</span></div></div>
        {!selected ? <EmptyState title="Seleccioná un producto" message="Vas a ver el stock y los lotes disponibles antes de confirmar el movimiento." /> : <>
          <ul className="detail-list">
            <li><span>Código de barras</span><strong className="mono">{selected.barcode}</strong></li>
            <li><span>Presentación</span><strong>{selected.presentation || '—'}</strong></li>
            <li><span>Stock total</span><strong>{lots.reduce((total, lot) => total + lot.current_quantity, 0)} u.</strong></li>
          </ul>
          <div className="table-scroll" style={{ marginTop: 18 }}>
            <table><thead><tr><th>Lote</th><th>Vence</th><th>Stock</th><th>Estado</th></tr></thead>
              <tbody>{sortedLots.map(lot => <tr key={lot.id}><td className="mono">{lot.lot_number}</td><td>{lot.expiration_date}</td><td>{lot.current_quantity} u.</td><td><StatusPill tone={lot.status === 'VENCIDO' ? 'danger' : lot.status === 'AGOTADO' ? 'neutral' : 'success'}>{lot.status}</StatusPill></td></tr>)}</tbody>
            </table>
          </div>
        </>}
        {suggestion.length > 0 && <div style={{ marginTop: 18 }}>
          <span className="eyebrow">SUGERENCIA FEFO</span>
          <ul className="detail-list">{suggestion.map(item => <li key={item.lot_id}><span>{item.lot_number} · vence {item.expiration_date}</span><strong>{item.suggested_quantity} u.</strong></li>)}</ul>
        </div>}
        {manualLot && <Notice tone="info">Lote elegido manualmente: {manualLot.lot_number}. {needsReason ? 'Necesitás un motivo para confirmar.' : ''}</Notice>}
      </aside>
    </div>
  </>
}
