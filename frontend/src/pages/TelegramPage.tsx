import { useEffect, useMemo, useState } from 'react'
import { api, type TelegramLinkCode, type TelegramLinkStatus } from '../api'
import { EmptyState, Notice, PageHeader, StatusPill } from '../components/Ui'

function formatDate(value: string): string {
  return new Date(value).toLocaleString('es-AR', { dateStyle: 'medium', timeStyle: 'short' })
}

function secondsLeft(expiresAt: string): number {
  return Math.max(0, Math.floor((new Date(expiresAt).getTime() - Date.now()) / 1000))
}

export function TelegramPage() {
  const [status, setStatus] = useState<TelegramLinkStatus | null>(null)
  const [code, setCode] = useState<TelegramLinkCode | null>(null)
  const [remaining, setRemaining] = useState(0)
  const [error, setError] = useState('')
  const [generating, setGenerating] = useState(false)
  const [copied, setCopied] = useState(false)

  const load = async () => setStatus(await api.telegramStatus())

  useEffect(() => {
    load().catch(err => setError(err instanceof Error ? err.message : 'No se pudo consultar el estado'))
  }, [])

  useEffect(() => {
    if (!code) return
    setRemaining(secondsLeft(code.expira_en))
    const timer = setInterval(() => {
      const left = secondsLeft(code.expira_en)
      setRemaining(left)
      if (left === 0) clearInterval(timer)
    }, 1000)
    return () => clearInterval(timer)
  }, [code])

  useEffect(() => {
    if (!copied) return
    const timer = setTimeout(() => setCopied(false), 2000)
    return () => clearTimeout(timer)
  }, [copied])

  const command = useMemo(() => (code ? `/vincular ${code.codigo}` : ''), [code])
  const deepLink = useMemo(
    () => (code && status?.bot_username ? `https://t.me/${status.bot_username}?start=${code.codigo}` : ''),
    [code, status],
  )

  const generate = async () => {
    setGenerating(true)
    setError('')
    try {
      const created = await api.telegramCode()
      setCode(created)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo generar el código')
    } finally {
      setGenerating(false)
    }
  }

  const copy = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
    } catch {
      setError('No se pudo copiar el código. Copialo manualmente.')
    }
  }

  const minutes = String(Math.floor(remaining / 60)).padStart(2, '0')
  const seconds = String(remaining % 60).padStart(2, '0')
  const expired = code !== null && remaining === 0

  return <>
    <PageHeader
      eyebrow="ASISTENTE"
      title="Telegram"
      description="Vinculá tu cuenta para consultar existencias y caducidades desde el bot."
      action={status?.vinculado ? undefined : <button className="primary-button" onClick={generate} disabled={generating}>{generating ? 'Generando…' : 'Generar código'}</button>}
    />
    {error && <Notice>{error}</Notice>}

    <div className="split-panel">
      <div className="panel table-panel">
        <div className="table-heading">
          <div><h2>Estado del vínculo</h2><span>{status?.bot_username ? `@${status.bot_username}` : 'Bot de Telegram'}</span></div>
          {status && <StatusPill tone={status.vinculado ? 'success' : 'neutral'}>{status.vinculado ? 'Vinculado' : 'Sin vincular'}</StatusPill>}
        </div>

        {status?.vinculado ? <div className="telegram-linked">
          <strong>Tu cuenta ya está vinculada</strong>
          <p>Desde {status.vinculado_en ? formatDate(status.vinculado_en) : 'este chat'} podés escribirle al bot y consultar el inventario de tu sucursal.</p>
          {status.bot_username && <a className="primary-button" href={`https://t.me/${status.bot_username}`} target="_blank" rel="noreferrer">Abrir Telegram</a>}
        </div> : <>
          {!code && <EmptyState title="Todavía no generaste un código" message="Generá un código de un solo uso y enviálo al bot en un chat privado." />}

          {code && <div className="link-code-card">
            <span className="eyebrow">CÓDIGO DE VINCULACIÓN</span>
            <p className="link-code" aria-live="polite">{code.codigo}</p>
            <p className={expired ? 'countdown expired' : 'countdown'}>
              {expired ? 'Código vencido, generá uno nuevo' : `Vence en ${minutes}:${seconds}`}
            </p>
            <div className="copy-row">
              <button className="secondary-button" onClick={() => copy(command)}>{copied ? 'Copiado' : 'Copiar comando'}</button>
              <button className="secondary-button" onClick={generate} disabled={generating}>{generating ? 'Generando…' : 'Generar otro código'}</button>
              {deepLink && !expired && <a className="primary-button" href={deepLink} target="_blank" rel="noreferrer">Abrir el bot</a>}
            </div>
            <p className="code-hint">Abrí Telegram, entrá al chat privado con {status?.bot_username ? `@${status.bot_username}` : 'el bot'} y enviá <code>{command}</code>.</p>
          </div>}
        </>}
      </div>

      <div className="panel table-panel">
        <div className="table-heading"><div><h2>Cómo funciona</h2><span>CU-14 · vinculación</span></div></div>
        <ol className="hint-list" style={{ marginTop: 18 }}>
          <li>Generá el código desde esta pantalla. Vale 10 minutos y un solo uso.</li>
          <li>Abrí el chat privado con el bot y enviá <code>/vincular CÓDIGO</code>.</li>
          <li>El bot valida el código y guarda el chat de tu cuenta.</li>
        </ol>
        <ul className="hint-list" style={{ marginTop: 18 }}>
          <li>Generar un código nuevo invalida el anterior.</li>
          <li>El código se guarda cifrado: nadie puede recuperarlo después.</li>
          <li>Un chat solo puede estar vinculado a una cuenta y viceversa.</li>
          <li>Después de 5 intentos fallidos el chat queda bloqueado 15 minutos.</li>
          <li>La vinculación solo funciona en chats privados, por seguridad.</li>
        </ul>
      </div>
    </div>
  </>
}
