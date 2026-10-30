from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.exceptions import BusinessRuleError
from app.models import Lot
from app.models.entities import LotStatus
from app.services.peps_service import allocate_fefo


def make_lot(lot_number: str, quantity: int, days: int) -> Lot:
    return Lot(
        medicine_id=1,
        branch_id=1,
        lot_number=lot_number,
        expiration_date=date.today() + timedelta(days=days),
        current_quantity=quantity,
        unit_cost=Decimal("100.00"),
        status=LotStatus.ACTIVE,
    )


def test_allocates_in_expiration_order() -> None:
    lots = [make_lot("A", 5, 10), make_lot("B", 20, 90)]

    allocations = allocate_fefo(lots, 8)

    assert [(item.lot.lot_number, item.quantity) for item in allocations] == [
        ("A", 5),
        ("B", 3),
    ]


def test_skips_lots_without_stock() -> None:
    lots = [make_lot("A", 0, 10), make_lot("B", 4, 90)]

    allocations = allocate_fefo(lots, 4)

    assert [(item.lot.lot_number, item.quantity) for item in allocations] == [("B", 4)]


def test_rejects_insufficient_stock() -> None:
    lots = [make_lot("A", 2, 10)]

    with pytest.raises(BusinessRuleError, match="Insufficient non-expired stock"):
        allocate_fefo(lots, 3)


def test_rejects_non_positive_quantity() -> None:
    with pytest.raises(BusinessRuleError, match="Quantity must be greater than zero"):
        allocate_fefo([make_lot("A", 2, 10)], 0)
