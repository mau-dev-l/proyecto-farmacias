
from datetime import date

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models.entities import Lot, LotStatus, Medicine


def consultar_stock(medicamento: str, sucursal_id: int) -> dict:
    """
    Consulta el stock disponible de un medicamento
    en una sucursal específica.

    Esta función es de solo lectura.
    """
    if not medicamento.strip():
        return {"error": "Debes indicar un medicamento."}

    if sucursal_id <= 0:
        return {"error": "La sucursal no es válida."}

    with SessionLocal() as db:
        consulta = (
            select(
                Medicine.name,
                func.coalesce(func.sum(Lot.current_quantity), 0),
            )
            .join(Lot, Lot.medicine_id == Medicine.id)
            .where(
                Medicine.name.ilike(f"%{medicamento.strip()}%"),
                Medicine.active.is_(True),
                Lot.branch_id == sucursal_id,
                Lot.status == LotStatus.ACTIVE,
                Lot.expiration_date >= date.today(),
                Lot.current_quantity > 0,
            )
            .group_by(Medicine.id, Medicine.name)
        )

        resultados = db.execute(consulta).all()

    if not resultados:
        return {
            "mensaje": "No se encontraron existencias disponibles.",
            "medicamento_buscado": medicamento,
            "sucursal_id": sucursal_id,
        }

    return {
        "sucursal_id": sucursal_id,
        "medicamentos": [
            {
                "nombre": nombre,
                "existencias": int(cantidad),
            }
            for nombre, cantidad in resultados
        ],
    }
