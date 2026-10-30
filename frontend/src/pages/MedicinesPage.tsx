import { useEffect, useState } from 'react'
import { api, type Medicine } from '../api'
import { EmptyState, Field, Modal, Notice, PageHeader, StatusPill } from '../components/Ui'

const emptyForm = { barcode: '', name: '', active_ingredient: '', presentation: '', sale_price: '', minimum_stock: '0' }

export function MedicinesPage() {
  const [items, setItems] = useState<Medicine[]>([])
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Medicine | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  const load = () => api.medicines(query).then(setItems).catch(err => setError(err.message))
  useEffect(() => { load() }, [query])

  const openNew = () => {
    setEditing(null)
    setForm(emptyForm)
    setError('')
    setModalOpen(true)
  }

  const openEdit = (medicine: Medicine) => {
    setEditing(medicine)
    setForm({
      barcode: medicine.barcode,
      name: medicine.name,
      active_ingredient: medicine.active_ingredient ?? '',
      presentation: medicine.presentation ?? '',
      sale_price: medicine.sale_price,
      minimum_stock: String(medicine.minimum_stock),
    })
    setError('')
    setModalOpen(true)
  }

  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        barcode: form.barcode,
        name: form.name,
        active_ingredient: form.active_ingredient || null,
        presentation: form.presentation || null,
        sale_price: Number(form.sale_price),
        minimum_stock: Number(form.minimum_stock),
      }
      if (editing) {
        await api.updateMedicine(editing.id, payload as Record<string, unknown>)
        setSuccess(`Medicamento ${form.name} actualizado.`)
      } else {
        await api.createMedicine(payload as Record<string, unknown>)
        setSuccess(`Medicamento ${form.name} creado.`)
      }
      setModalOpen(false)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el medicamento')
    } finally {
      setSaving(false)
    }
  }

  const deactivate = async (medicine: Medicine) => {
    setError('')
    try {
      await api.deleteMedicine(medicine.id)
      setSuccess(`Medicamento ${medicine.name} desactivado.`)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo desactivar el medicamento')
    }
  }

  return <>
    <PageHeader eyebrow="CATÁLOGO" title="Medicamentos" description="Mantené el catálogo limpio y listo para operar." action={<button className="primary-button" onClick={openNew}>+ Nuevo medicamento</button>} />
    {error && <Notice>{error}</Notice>}
    {success && <Notice tone="success">{success}</Notice>}
    <div className="toolbar"><label className="search-field"><span>⌕</span><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Buscar medicamento…" /></label><span className="toolbar-note">{items.length} activos</span></div>
    <div className="panel table-panel">
      <div className="table-heading"><div><h2>Catálogo activo</h2><span>Datos comerciales y de venta</span></div></div>
      {items.length === 0 ? <EmptyState title="Catálogo vacío" message="Cuando conectes la API, tus medicamentos aparecerán aquí." /> : <div className="table-scroll"><table><thead><tr><th>Medicamento</th><th>Código de barras</th><th>Presentación</th><th>Precio de venta</th><th>Stock mínimo</th><th>Estado</th><th /></tr></thead><tbody>{items.map(item => <tr key={item.id}>
        <td><strong>{item.name}</strong><small>{item.active_ingredient || 'Sin principio activo'}</small></td>
        <td className="mono">{item.barcode}</td>
        <td>{item.presentation || '—'}</td>
        <td>$ {Number(item.sale_price).toLocaleString('es-AR')}</td>
        <td>{item.minimum_stock} u.</td>
        <td><StatusPill tone={item.active ? 'success' : 'danger'}>{item.active ? 'Activo' : 'Inactivo'}</StatusPill></td>
        <td><div className="inline-actions"><button className="secondary-button" onClick={() => openEdit(item)}>Editar</button><button className="danger-button" onClick={() => deactivate(item)}>Desactivar</button></div></td>
      </tr>)}</tbody></table></div>}
    </div>

    <Modal open={modalOpen} title={editing ? 'Editar medicamento' : 'Nuevo medicamento'} description="El código de barras debe ser único." onClose={() => setModalOpen(false)}>
      <form onSubmit={save}>
        <div className="form-grid">
          <Field label="Código de barras"><input value={form.barcode} onChange={event => setForm({ ...form, barcode: event.target.value })} required maxLength={30} /></Field>
          <Field label="Nombre"><input value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} required maxLength={150} /></Field>
          <Field label="Principio activo"><input value={form.active_ingredient} onChange={event => setForm({ ...form, active_ingredient: event.target.value })} maxLength={150} /></Field>
          <Field label="Presentación"><input value={form.presentation} onChange={event => setForm({ ...form, presentation: event.target.value })} maxLength={100} /></Field>
          <Field label="Precio de venta"><input type="number" min="0" step="0.01" value={form.sale_price} onChange={event => setForm({ ...form, sale_price: event.target.value })} required /></Field>
          <Field label="Stock mínimo"><input type="number" min="0" value={form.minimum_stock} onChange={event => setForm({ ...form, minimum_stock: event.target.value })} required /></Field>
        </div>
        <div className="form-actions"><button type="button" className="secondary-button" onClick={() => setModalOpen(false)}>Cancelar</button><button className="primary-button" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button></div>
      </form>
    </Modal>
  </>
}
