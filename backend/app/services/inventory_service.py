from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import (
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)
from app.models import Alert, Lot, Medicine, Movement, User
from app.models.entities import AlertType, LotStatus, MovementType
from app.repositories import alerts as alerts_repository
from app.repositories import lots as lots_repository
from app.repositories import medicines as medicines_repository
from app.repositories import movements as movements_repository
from app.repositories import suppliers as suppliers_repository
from app.schemas.inventory import (
    EntryRequest,
    InventoryItem,
    InventoryLot,
    KardexEntry,
    SaleRequest,
    SuggestedLot,
)
from app.services import peps_service


def resolve_branch(current_user: User, branch_id: int | None) -> int:
    if branch_id is not None and branch_id != current_user.branch_id and current_user.role.value != "ADMIN":
        raise AuthorizationError("Branch access denied")
    return branch_id or current_user.branch_id


def list_inventory(
    db: Session,
    current_user: User,
    branch_id: int | None,
    q: str | None,
) -> list[InventoryItem]:
    branch = resolve_branch(current_user, branch_id)
    rows = medicines_repository.list_stock_by_branch(db, branch, q)
    lots_by_medicine: dict[int, list[Lot]] = {}
    for lot in lots_repository.list_active_for_branch(db, branch):
        lots_by_medicine.setdefault(lot.medicine_id, []).append(lot)
    return [
        InventoryItem(
            medicine_id=row.medicine_id,
            name=row.name,
            barcode=row.barcode,
            minimum_stock=row.minimum_stock,
            total_stock=row.total_stock,
            lots=[
                InventoryLot.model_validate(lot)
                for lot in lots_by_medicine.get(row.medicine_id, [])
            ],
        )
        for row in rows
    ]


def list_lots(
    db: Session,
    current_user: User,
    medicine_id: int,
    branch_id: int | None,
) -> list[Lot]:
    branch = resolve_branch(current_user, branch_id)
    return lots_repository.list_for_medicine(db, medicine_id, branch)


def register_entry(db: Session, current_user: User, payload: EntryRequest) -> Movement:
    if payload.expiration_date < date.today():
        raise BusinessRuleError("Expiration date cannot be in the past")

    medicine = medicines_repository.get(db, payload.medicine_id)
    if medicine is None or not medicine.active:
        raise NotFoundError("Medicine not found")

    if payload.supplier_id is not None and suppliers_repository.get(db, payload.supplier_id) is None:
        raise NotFoundError("Supplier not found")

    lot = lots_repository.get_by_number(
        db,
        payload.medicine_id,
        current_user.branch_id,
        payload.lot_number,
    )
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
        lots_repository.add(db, lot)
    else:
        if lot.expiration_date != payload.expiration_date:
            raise ConflictError("Lot number already exists with a different expiration date")
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
    movements_repository.add(db, movement)
    db.commit()
    db.refresh(movement)
    return movement


def suggest_peps(
    db: Session,
    current_user: User,
    medicine_id: int,
    quantity: int,
) -> list[SuggestedLot]:
    return peps_service.suggest(db, medicine_id, current_user.branch_id, quantity)


def register_sale(db: Session, current_user: User, payload: SaleRequest) -> list[Movement]:
    medicine = medicines_repository.get(db, payload.medicine_id)
    if medicine is None or not medicine.active:
        raise NotFoundError("Medicine not found")

    is_waste = payload.movement_type == MovementType.WASTE
    today = date.today()
    candidates = lots_repository.list_fefo(
        db,
        payload.medicine_id,
        current_user.branch_id,
        include_expired=is_waste,
        lock=payload.lot_id is None,
    )

    if payload.lot_id is not None:
        lot = lots_repository.get_for_update(db, payload.lot_id)
        if lot is None or lot.medicine_id != payload.medicine_id or lot.branch_id != current_user.branch_id:
            raise NotFoundError("Lot not found")
        if not is_waste and lot.expiration_date < today:
            raise BusinessRuleError("Expired lots cannot be sold; register them as waste")
        first = candidates[0] if candidates else None
        if (first is None or first.id != lot.id) and not payload.reason:
            raise BusinessRuleError("A reason is required to override the PEPS suggestion")
        candidates = [lot]

    allocations = peps_service.allocate_fefo(candidates, payload.quantity)

    movements: list[Movement] = []
    for allocation in allocations:
        lot = allocation.lot
        lot.current_quantity -= allocation.quantity
        if lot.current_quantity == 0:
            lot.status = LotStatus.DEPLETED
        movement = Movement(
            lot_id=lot.id,
            user_id=current_user.id,
            movement_type=payload.movement_type,
            quantity=allocation.quantity,
            lot_balance=lot.current_quantity,
            unit_cost=lot.unit_cost,
            reason=payload.reason,
        )
        movements_repository.add(db, movement)
        movements.append(movement)

    db.flush()
    total_stock = sum(
        lot.current_quantity
        for lot in lots_repository.list_fefo(db, payload.medicine_id, current_user.branch_id)
    )
    if total_stock < medicine.minimum_stock:
        target_lot = allocations[0].lot
        if not alerts_repository.exists_unread_for_medicine(db, payload.medicine_id, AlertType.LOW_STOCK):
            alerts_repository.add(
                db,
                Alert(
                    lot_id=target_lot.id,
                    alert_type=AlertType.LOW_STOCK,
                    threshold_days=None,
                ),
            )

    db.commit()
    for movement in movements:
        db.refresh(movement)
    return movements


def list_kardex(
    db: Session,
    current_user: User,
    medicine_id: int | None,
    lot_id: int | None,
    desde: date | None,
    hasta: date | None,
) -> list[KardexEntry]:
    if desde is not None and hasta is not None and hasta < desde:
        raise BusinessRuleError("End date cannot be earlier than start date")
    rows = movements_repository.list_kardex(
        db,
        current_user.branch_id,
        medicine_id=medicine_id,
        lot_id=lot_id,
        desde=desde,
        hasta=hasta,
    )
    return [KardexEntry.model_validate(row, from_attributes=True) for row in rows]
