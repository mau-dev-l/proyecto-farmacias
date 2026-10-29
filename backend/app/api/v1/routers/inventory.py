from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Branch, Lot, Medicine, Movement, User
from app.models.entities import LotStatus, MovementType
from app.schemas.inventory import (
    EntryRequest,
    InventoryItem,
    LotResponse,
    MovementResponse,
    SaleRequest,
    SuggestedLot,
)

router = APIRouter(tags=["inventory"])


def selected_branch(current_user: User, branch_id: int | None) -> int:
    if branch_id is not None and branch_id != current_user.branch_id and current_user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Branch access denied")
    return branch_id or current_user.branch_id


@router.get("/inventario", response_model=list[InventoryItem])
def inventory(
    branch_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InventoryItem]:
    branch = selected_branch(current_user, branch_id)
    total_stock = func.coalesce(func.sum(Lot.current_quantity), 0).label("total_stock")
    query = (
        select(Medicine.id, Medicine.name, Medicine.barcode, Medicine.minimum_stock, total_stock)
        .outerjoin(Lot, (Lot.medicine_id == Medicine.id) & (Lot.branch_id == branch) & (Lot.status == LotStatus.ACTIVE))
        .where(Medicine.active.is_(True))
        .group_by(Medicine.id)
        .order_by(Medicine.name)
    )
    if q:
        query = query.where(Medicine.name.ilike(f"%{q}%"))
    return [InventoryItem(medicine_id=row.id, name=row.name, barcode=row.barcode, minimum_stock=row.minimum_stock, total_stock=row.total_stock) for row in db.execute(query)]


@router.get("/medicamentos/{medicine_id}/lotes", response_model=list[LotResponse])
def medicine_lots(
    medicine_id: int,
    branch_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Lot]:
    branch = selected_branch(current_user, branch_id)
    return list(db.scalars(select(Lot).where(Lot.medicine_id == medicine_id, Lot.branch_id == branch).order_by(Lot.expiration_date, Lot.id)))


@router.post("/movimientos/entrada", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
def register_entry(
    payload: EntryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Movement:
    medicine = db.get(Medicine, payload.medicine_id)
    if medicine is None or not medicine.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    lot = db.scalar(select(Lot).where(Lot.medicine_id == payload.medicine_id, Lot.branch_id == current_user.branch_id, Lot.lot_number == payload.lot_number))
    if lot is None:
        lot = Lot(
            medicine_id=payload.medicine_id,
            branch_id=current_user.branch_id,
            supplier_id=payload.supplier_id,
            lot_number=payload.lot_number,
            expiration_date=payload.expiration_date,
            current_quantity=payload.quantity,
            unit_cost=payload.unit_cost,
            status=LotStatus.ACTIVE,
        )
        db.add(lot)
        db.flush()
    else:
        lot.current_quantity += payload.quantity
        lot.status = LotStatus.ACTIVE
    movement = Movement(
        lot_id=lot.id,
        user_id=current_user.id,
        movement_type=MovementType.ENTRY,
        quantity=payload.quantity,
        lot_balance=lot.current_quantity,
        unit_cost=lot.unit_cost,
        reason=payload.reason,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get("/movimientos/peps-sugerido", response_model=list[SuggestedLot])
def peps_suggestion(
    medicine_id: int,
    quantity: int = Query(gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SuggestedLot]:
    lots = list(db.scalars(select(Lot).where(Lot.medicine_id == medicine_id, Lot.branch_id == current_user.branch_id, Lot.current_quantity > 0, Lot.expiration_date >= date.today()).order_by(Lot.expiration_date, Lot.id)))
    remaining = quantity
    suggestions: list[SuggestedLot] = []
    for lot in lots:
        if remaining <= 0:
            break
        suggested = min(remaining, lot.current_quantity)
        suggestions.append(SuggestedLot(lot_id=lot.id, lot_number=lot.lot_number, expiration_date=lot.expiration_date, available_quantity=lot.current_quantity, suggested_quantity=suggested))
        remaining -= suggested
    if remaining:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient non-expired stock")
    return suggestions


@router.post("/movimientos/salida", response_model=list[MovementResponse])
def register_sale(
    payload: SaleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Movement]:
    lots = list(db.scalars(select(Lot).where(Lot.medicine_id == payload.medicine_id, Lot.branch_id == current_user.branch_id, Lot.current_quantity > 0, Lot.expiration_date >= date.today()).order_by(Lot.expiration_date, Lot.id).with_for_update()))
    remaining = payload.quantity
    movements: list[Movement] = []
    for lot in lots:
        if remaining <= 0:
            break
        taken = min(remaining, lot.current_quantity)
        lot.current_quantity -= taken
        if lot.current_quantity == 0:
            lot.status = LotStatus.DEPLETED
        movement = Movement(lot_id=lot.id, user_id=current_user.id, movement_type=MovementType.SALE, quantity=taken, lot_balance=lot.current_quantity, unit_cost=lot.unit_cost, reason=payload.reason)
        db.add(movement)
        movements.append(movement)
        remaining -= taken
    if remaining:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient non-expired stock")
    db.commit()
    for movement in movements:
        db.refresh(movement)
    return movements


@router.get("/kardex", response_model=list[MovementResponse])
def kardex(
    medicine_id: int | None = None,
    lot_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Movement]:
    query = select(Movement).join(Lot, Movement.lot_id == Lot.id).where(Lot.branch_id == current_user.branch_id).order_by(Movement.created_at.desc())
    if medicine_id is not None:
        query = query.where(Lot.medicine_id == medicine_id)
    if lot_id is not None:
        query = query.where(Movement.lot_id == lot_id)
    return list(db.scalars(query))
