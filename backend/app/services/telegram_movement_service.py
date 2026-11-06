
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lot, Medicine, Movement
from app.services.telegram_identity_service import (
    obtener_identidad_telegram,
)


@dataclass(frozen=True)
class UltimoMovimientoTelegram:
    id: int
    medicamento: str
    lote: str
    tipo: str
    cantidad: int
    saldo_lote: int
    fecha: datetime
    motivo: str | None


def consultar_ultimo_movimiento_telegram(
    db: Session,
    chat_id: int,
) -> UltimoMovimientoTelegram | list | None:
    identidad = obtener_identidad_telegram(db, chat_id)

    if identidad is None:
        return None

    consulta = (
        select(
            Movement.id,
            Medicine.name,
            Lot.lot_number,
            Movement.movement_type,
            Movement.quantity,
            Movement.lot_balance,
            Movement.created_at,
            Movement.reason,
        )
        .join(Lot, Movement.lot_id == Lot.id)
        .join(Medicine, Lot.medicine_id == Medicine.id)
        .where(Lot.branch_id == identidad.sucursal_id)
        .order_by(
            Movement.created_at.desc(),
            Movement.id.desc(),
        )
        .limit(1)
    )

    fila = db.execute(consulta).first()

    if fila is None:
        return []

    return UltimoMovimientoTelegram(
        id=fila[0],
        medicamento=fila[1],
        lote=fila[2],
        tipo=fila[3].value,
        cantidad=fila[4],
        saldo_lote=fila[5],
        fecha=fila[6],
        motivo=fila[7],
    )
