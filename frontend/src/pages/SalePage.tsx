import { MovementForm } from '../components/MovementForm'
import { PageHeader } from '../components/Ui'

export function SalePage() {
  return <>
    <PageHeader eyebrow="MOVIMIENTOS" title="Registrar salida" description="Registrá ventas y mermas. El stock sale por FEFO, del lote que vence primero." />
    <MovementForm kind="SALIDA" />
  </>
}
