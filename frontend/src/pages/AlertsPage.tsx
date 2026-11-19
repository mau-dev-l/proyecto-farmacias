import { useEffect, useState } from 'react'
import { api, type Alert, type AlertConfiguration } from '../api'
import { useAuth } from '../auth'
import { Icons } from '../components/icons'
import { EmptyState, Field, Notice, PageHeader, Tabs } from '../components/Ui'

type AlertTab = 'todas' | Alert['alert_type']

const labels: Record<Alert['alert_type'], string> = { PROXIMO_VENCER: 'Próximo a vencer', VENCIDO: 'Vencido', STOCK_MINIMO: 'Stock mínimo' }

const tabOptions: { value: AlertTab; label: string; icon: React.ReactNode }[] = [
  { value: 'todas', label: 'Todas', icon: <Icons.alert aria-hidden="true" /> },
  { value: 'PROXIMO_VENCER', label: 'Próximos a vencer', icon: <Icons.clock aria-hidden="true" /> },
  { value: 'VENCIDO', label: 'Vencidos', icon: <Icons.expiring aria-hidden="true" /> },
  { value: 'STOCK_MINIMO', label: 'Stock mínimo', icon: <Icons.warning aria-hidden="true" /> },
]

export function AlertsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'ADMIN'
  const [tab, setTab] = useState<AlertTab>('todas')
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [config, setConfig] = useState<AlertConfiguration | null>(null)
  const [thresholdsInput, setThresholdsInput] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [generating, setGenerating] = useState(false)

  const loadAlerts = async () => {
    setLoading(true)
    setError('')
    try {
      setAlerts(await api.alerts({ read: false, tipo: tab === 'todas' ? undefined : tab }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron cargar las alertas')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadAlerts() }, [tab])

  useEffect(() => {
    api.alertConfig()
      .then(cfg => { setConfig(cfg); setThresholdsInput(cfg.thresholds.join(', ')) })
      .catch(() => setConfig(null))
  }, [])

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
      await loadAlerts()
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
    <PageHeader
      eyebrow="SEGUIMIENTO"
      title="Alertas"
      description="Revisá vencimientos y faltantes de stock de tu sucursal."
      action={isAdmin ? <button className="primary-button" onClick={generate} disabled={generating}><Icons.alert className="btn-icon" aria-hidden="true" />{generating ? 'Generando…' : 'Generar alertas'}</button> : undefined}
    />
    {error && <Notice>{error}</Notice>}
    {success && <Notice tone="success">{success}</Notice>}

    <Tabs value={tab} onChange={setTab} options={tabOptions} />

    <div className="split-panel wide-left">
      <div className="panel table-panel">
        <div className="table-heading"><div><h2>{tab === 'todas' ? 'Alertas pendientes' : labels[tab]}</h2><span>{alerts.length} sin leer</span></div></div>
        {loading ? <div className="loading-row">Cargando alertas…</div> : alerts.length === 0 ? <EmptyState title="Todo bajo control" message="No hay alertas pendientes para este filtro." /> : <div className="alert-list">{alerts.map(alert => <div className="alert-list-row" key={alert.id}>
          <span className={`alert-symbol ${alert.alert_type === 'VENCIDO' ? 'red' : 'amber'}`}>{alert.alert_type === 'STOCK_MINIMO' ? <Icons.warning aria-hidden="true" /> : <Icons.clock aria-hidden="true" />}</span>
          <div className="alert-copy">
            <strong>{labels[alert.alert_type]} · {alert.medicine_name}</strong>
            <p>Lote {alert.lot_number} · vence {alert.expiration_date} · {alert.quantity} u. restantes · {alert.days_remaining} días{alert.threshold_days ? ` · umbral ${alert.threshold_days} días` : ''}</p>
          </div>
          <button className="secondary-button" onClick={() => markRead(alert.id)}><Icons.check className="btn-icon" aria-hidden="true" />Marcar leída</button>
        </div>)}</div>}
      </div>

      <div className="panel table-panel">
        <div className="table-heading"><div><h2>Umbrales de vencimiento</h2><span>{config ? config.thresholds.join(', ') : '—'} días</span></div></div>
        {isAdmin ? <form onSubmit={saveConfig}>
          <Field label="Días de anticipación" hint="Separá varios valores con comas, por ejemplo 90, 60, 30.">
            <input value={thresholdsInput} onChange={event => setThresholdsInput(event.target.value)} placeholder="90, 60, 30" />
          </Field>
          <div className="form-actions"><button className="primary-button" disabled={saving}><Icons.settings className="btn-icon" aria-hidden="true" />{saving ? 'Guardando…' : 'Guardar configuración'}</button></div>
        </form> : <ul className="detail-list">
          <li><span>Umbrales activos</span><strong>{config ? `${config.thresholds.join(', ')} días` : '—'}</strong></li>
          <li><span>Configuración</span><strong>Solo administración</strong></li>
        </ul>}
        <ul className="hint-list" style={{ marginTop: 18 }}>
          <li>El job diario crea una alerta por cada umbral alcanzado.</li>
          <li>Las alertas no se duplican para el mismo lote y umbral.</li>
          <li>Los lotes vencidos se marcan automáticamente como vencidos.</li>
        </ul>
      </div>
    </div>
  </>
}
