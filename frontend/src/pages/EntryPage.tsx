import { MovementForm } from '../components/MovementForm'
import { PageHeader } from '../components/Ui'

export function EntryPage() {
  return <>
    <PageHeader eyebrow="MOVIMIENTOS" title="Registrar entrada" description="Cargá compras y reposición de stock con trazabilidad por lote." />
    <MovementForm kind="ENTRADA" />
  </>
}
