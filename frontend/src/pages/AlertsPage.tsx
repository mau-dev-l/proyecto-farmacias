import { useEffect, useState } from 'react'
import { api, type Alert, type AlertConfiguration } from '../api'
import { EmptyState, Field, Notice, PageHeader, StatusPill } from '../components/Ui'

const labels: Record<Alert['alert_type'], string> = { PROXIMO_VENCER: 'Próximo a vencer', VENCIDO: 'Vencido', STOCK_MINIMO: 'Stock mínimo' }

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [config, setConfig] = useState<AlertConfiguration | null>(null)
  const [thresholdsInput, setThresholdsInput] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [saving, setSaving] = useState(false)
  const [generating, setGenerating] = useState(false)

  const load = async () => {
    const [list, cfg] = await Promise.all([api.alerts(false), api.alertConfig()])
    setAlerts(list)
    setConfig(cfg)
    setThresholdsInput(cfg.thresholds.join(', '))
  }

  useEffect(() => { load().catch(err => setError(err.message)) }, [])

  const saveConfig = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const thresholds = thresholdsInput.split(',').map(value => Number(value.trim())).filter(value => !Number.isNaN(value))
      if (thresholds.length === 0) throw new Error('Ingresá al menos un umbral')
      const updated = await api.setAlertConfig(thresholds)
      setConfig(updated)
      setThresholdsInput(updated.thresholds.join(', '))
      setSuccess('Configuración de alertas guardada.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar la configuración')
    } finally {
      setSaving(false)
    }
  }

  const generate = async () => {
    setGenerating(true)
    setError('')
    try {
      const result = await api.generateAlerts()
      setSuccess(`Se generaron ${result.created} alerta(s) nuevas.`)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo generar alertas')
    } finally {
      setGenerating(false)
    }
  }

  const markRead = async (id: number) => {
    await api.markAlertRead(id)
    setAlerts(current => current.filter(alert => alert.id !== id))
  }

  return <>
    <PageHeader eyebrow="SEGUIMIENTO" title="Alertas" description="Priorizá lo que necesita una decisión hoy." action={<button className="primary-button" onClick={generate} disabled={generating}>{generating ? 'Generando…' : 'Generar alertas'}</button>} />
    {error && <Notice>{error}</Notice>}
    {success && <Notice tone="success">{success}</Notice>}

    <div className="split-panel">
      <div className="panel table-panel">
        <div className="table-heading"><div><h2>Alertas pendientes</h2><span>{alerts.length} sin leer</span></div></div>
        {alerts.length === 0 ? <EmptyState title="Todo bajo control" message="No hay alertas pendientes para esta sucursal." /> : <div className="alert-list">{alerts.map(alert => <div className="alert-list-row" key={alert.id}>
          <span className={`alert-symbol ${alert.alert_type === 'VENCIDO' ? 'red' : 'amber'}`}>{alert.alert_type === 'STOCK_MINIMO' ? '!' : '◷'}</span>
          <div className="alert-copy">
            <strong>{labels[alert.alert_type]} · {alert.medicine_name}</strong>
            <p>Lote {alert.lot_number} · vence {alert.expiration_date} · {alert.quantity} u. restantes · {alert.days_remaining} días{alert.threshold_days ? ` · umbral ${alert.threshold_days} días` : ''}</p>
          </div>
          <StatusPill tone={alert.alert_type === 'VENCIDO' ? 'danger' : alert.alert_type === 'STOCK_MINIMO' ? 'warning' : 'warning'}>{labels[alert.alert_type]}</StatusPill>
          <button className="secondary-button" onClick={() => markRead(alert.id)}>Marcar leída</button>
        </div>)}</div>}
      </div>

      <div className="panel table-panel">
        <div className="table-heading"><div><h2>Umbrales de vencimiento</h2><span>{config ? config.thresholds.join(', ') : '—'} días</span></div></div>
        <form onSubmit={saveConfig}>
          <Field label="Días de anticipación" hint="Separá varios valores con comas, por ejemplo 90, 60, 30.">
            <input value={thresholdsInput} onChange={event => setThresholdsInput(event.target.value)} placeholder="90, 60, 30" />
          </Field>
          <div className="form-actions"><button className="primary-button" disabled={saving}>{saving ? 'Guardando…' : 'Guardar configuración'}</button></div>
        </form>
        <ul className="hint-list" style={{ marginTop: 18 }}>
          <li>El job diario crea una alerta por cada umbral alcanzado.</li>
          <li>Las alertas no se duplican para el mismo lote y umbral.</li>
          <li>Los lotes vencidos se marcan automáticamente como vencidos.</li>
        </ul>
      </div>
    </div>
  </>
}
