from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Lot, Movement, User
from app.schemas.inventory import (
    EntryRequest,
    InventoryItem,
    KardexEntry,
    LotResponse,
    MovementResponse,
    SaleRequest,
    SuggestedLot,
)
from app.services import inventory_service

router = APIRouter(tags=["inventory"])


@router.get("/inventario", response_model=list[InventoryItem])
def inventory(
    branch_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InventoryItem]:
    return inventory_service.list_inventory(db, current_user, branch_id, q)


@router.get("/medicamentos/{medicine_id}/lotes", response_model=list[LotResponse])
def medicine_lots(
    medicine_id: int,
    branch_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Lot]:
    return inventory_service.list_lots(db, current_user, medicine_id, branch_id)


@router.post(
    "/movimientos/entrada",
    response_model=MovementResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_entry(
    payload: EntryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Movement:
    return inventory_service.register_entry(db, current_user, payload)


@router.get("/movimientos/peps-sugerido", response_model=list[SuggestedLot])
def peps_suggestion(
    medicine_id: int,
    quantity: int = Query(gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SuggestedLot]:
    return inventory_service.suggest_peps(db, current_user, medicine_id, quantity)


@router.post("/movimientos/salida", response_model=list[MovementResponse])
def register_sale(
    payload: SaleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Movement]:
    return inventory_service.register_sale(db, current_user, payload)


@router.get("/kardex", response_model=list[KardexEntry])
def kardex(
    medicine_id: int | None = None,
    lot_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[KardexEntry]:
    return inventory_service.list_kardex(db, current_user, medicine_id, lot_id, desde, hasta)
