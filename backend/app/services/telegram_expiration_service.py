
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lot, Medicine
from app.models.entities import LotStatus
from app.services.telegram_identity_service import (
    obtener_identidad_telegram,
)


@dataclass(frozen=True)
class MedicamentoProximoAVencer:
    nombre: str
    lote: str
    fecha_caducidad: date
    dias_restantes: int
    cantidad: int


def consultar_caducidades_telegram(
    db: Session,
    chat_id: int,
    dias: int = 30,
) -> list[MedicamentoProximoAVencer] | None:
    """
    Consulta lotes próximos a vencer en la sucursal
    autorizada del usuario de Telegram.

    None: usuario no autorizado.
    []: no hay lotes próximos a vencer.
    """

    identidad = obtener_identidad_telegram(db, chat_id)

    if identidad is None:
        return None

    if (
        isinstance(dias, bool)
        or not isinstance(dias, int)
        or dias < 0
        or dias > 365
    ):
        return []

    hoy = date.today()
    fecha_limite = hoy + timedelta(days=dias)

    consulta = (
        select(
            Medicine.name,
            Lot.lot_number,
            Lot.expiration_date,
            Lot.current_quantity,
        )
        .join(
            Lot,
            Lot.medicine_id == Medicine.id,
        )
        .where(
            Medicine.active.is_(True),
            Lot.branch_id == identidad.sucursal_id,
            Lot.status == LotStatus.ACTIVE,
            Lot.current_quantity > 0,
            Lot.expiration_date >= hoy,
            Lot.expiration_date <= fecha_limite,
        )
        .order_by(
            Lot.expiration_date,
            Medicine.name,
        )
        .limit(20)
    )

    resultados = db.execute(consulta).all()

    return [
        MedicamentoProximoAVencer(
            nombre=fila[0],
            lote=fila[1],
            fecha_caducidad=fila[2],
            dias_restantes=(fila[2] - hoy).days,
            cantidad=int(fila[3]),
        )
        for fila in resultados
    ]
