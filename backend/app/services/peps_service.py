from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.models import Lot
from app.repositories import lots as lots_repository
from app.schemas.inventory import SuggestedLot


@dataclass(frozen=True)
class Allocation:
    lot: Lot
    quantity: int


def allocate_fefo(lots: Sequence[Lot], quantity: int) -> list[Allocation]:
    """Allocate stock from the earliest-expiring lots first.

    The caller is responsible for ordering and filtering the lots. This function
    is intentionally pure so the PEPS rule can be tested without a database.
    """
    if quantity <= 0:
        raise BusinessRuleError("Quantity must be greater than zero")

    allocations: list[Allocation] = []
    remaining = quantity
    for lot in lots:
        if remaining <= 0:
            break
        taken = min(remaining, lot.current_quantity)
        if taken <= 0:
            continue
        allocations.append(Allocation(lot=lot, quantity=taken))
        remaining -= taken

    if remaining:
        raise BusinessRuleError("Insufficient non-expired stock")
    return allocations


def suggest(db: Session, medicine_id: int, branch_id: int, quantity: int) -> list[SuggestedLot]:
    lots = lots_repository.list_fefo(db, medicine_id, branch_id)
    allocations = allocate_fefo(lots, quantity)
    return [
        SuggestedLot(
            lot_id=allocation.lot.id,
            lot_number=allocation.lot.lot_number,
            expiration_date=allocation.lot.expiration_date,
            available_quantity=allocation.lot.current_quantity,
            suggested_quantity=allocation.quantity,
        )
        for allocation in allocations
    ]
