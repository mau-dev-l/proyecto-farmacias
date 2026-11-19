"""Demo dataset for screenshots and report walkthroughs.

The data is inserted through the service layer (``inventory_service``), not with
raw SQL, so lot balances, PEPS allocation, low-stock alerts and the kardex stay
consistent with what the application would produce in real use.

Usage, from the ``backend`` directory:

    python -m scripts.demo_data            # insert demo data (idempotent)
    python -m scripts.demo_data --clean    # remove demo data only

What it creates:

* 9 extra medicines that do not exist in the catalog yet.
* Entry lots with staggered expirations: some expire within the 30/60/90 day
  alert thresholds, the rest are far enough out to look healthy.
* Sales and waste movements spread over the last two months, alternating the
  admin and the employee so the kardex shows different user names.
* Movement timestamps are backdated in chronological order, so the kardex
  balances stay monotonic when read as a timeline.

``--clean`` only removes the medicines whose barcode starts with
``7790000001`` plus the specific demo lots created on the pre-existing
medicines. It never touches the original seed catalog.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Alert, Lot, Medicine, Movement, Supplier, User
from app.models.entities import MovementType
from app.schemas.inventory import EntryRequest, SaleRequest
from app.services import alert_service, inventory_service

DEMO_BARCODE_PREFIX = "7790000001"

# Days of history used to spread the movements. Reports filter by date range, so
# the timeline has to look like a running branch, not a single import batch.
CATALOG: tuple[dict, ...] = (
    {
        "barcode": "779000000101",
        "name": "Loratadina 10 mg",
        "active_ingredient": "Loratadina",
        "presentation": "Caja x 10 comprimidos",
        "sale_price": Decimal("2800.00"),
        "minimum_stock": 12,
        "lots": (
            {"number": "LOR-2701", "expires_in": 18, "quantity": 36, "cost": Decimal("1350.00"), "days_ago": 55},
            {"number": "LOR-2802", "expires_in": 400, "quantity": 48, "cost": Decimal("1400.00"), "days_ago": 20},
        ),
    },
    {
        "barcode": "779000000102",
        "name": "Diclofenac 50 mg",
        "active_ingredient": "Diclofenac sódico",
        "presentation": "Caja x 20 comprimidos",
        "sale_price": Decimal("3900.00"),
        "minimum_stock": 10,
        "lots": (
            {"number": "DIC-2701", "expires_in": 27, "quantity": 28, "cost": Decimal("1900.00"), "days_ago": 60},
        ),
    },
    {
        "barcode": "779000000103",
        "name": "Omeprazol 20 mg",
        "active_ingredient": "Omeprazol",
        "presentation": "Caja x 14 cápsulas",
        "sale_price": Decimal("5200.00"),
        "minimum_stock": 15,
        "lots": (
            {"number": "OME-2701", "expires_in": 55, "quantity": 42, "cost": Decimal("2600.00"), "days_ago": 70},
            {"number": "OME-2802", "expires_in": 500, "quantity": 30, "cost": Decimal("2650.00"), "days_ago": 12},
        ),
    },
    {
        "barcode": "779000000104",
        "name": "Salbutamol 100 mcg",
        "active_ingredient": "Salbutamol",
        "presentation": "Inhalador 200 dosis",
        "sale_price": Decimal("8900.00"),
        "minimum_stock": 6,
        "lots": (
            {"number": "SAL-2701", "expires_in": 85, "quantity": 14, "cost": Decimal("5200.00"), "days_ago": 40},
        ),
    },
    {
        "barcode": "779000000105",
        "name": "Metformina 850 mg",
        "active_ingredient": "Metformina clorhidrato",
        "presentation": "Caja x 30 comprimidos",
        "sale_price": Decimal("6400.00"),
        "minimum_stock": 10,
        "lots": (
            {"number": "MET-2801", "expires_in": 330, "quantity": 60, "cost": Decimal("3100.00"), "days_ago": 45},
        ),
    },
    {
        "barcode": "779000000106",
        "name": "Enalapril 10 mg",
        "active_ingredient": "Enalapril maleato",
        "presentation": "Caja x 30 comprimidos",
        "sale_price": Decimal("4700.00"),
        "minimum_stock": 10,
        "lots": (
            {"number": "ENA-2801", "expires_in": 280, "quantity": 45, "cost": Decimal("2200.00"), "days_ago": 38},
        ),
    },
    {
        "barcode": "779000000107",
        "name": "Clonazepam 2 mg",
        "active_ingredient": "Clonazepam",
        "presentation": "Caja x 30 comprimidos",
        "sale_price": Decimal("7300.00"),
        "minimum_stock": 5,
        "lots": (
            {"number": "CLO-2801", "expires_in": 450, "quantity": 12, "cost": Decimal("3900.00"), "days_ago": 30},
        ),
    },
    {
        "barcode": "779000000108",
        "name": "Insulina NPH 100 UI",
        "active_ingredient": "Insulina humana",
        "presentation": "Frasco 10 ml",
        "sale_price": Decimal("15400.00"),
        "minimum_stock": 4,
        "lots": (
            {"number": "INS-2701", "expires_in": 65, "quantity": 8, "cost": Decimal("9500.00"), "days_ago": 25},
        ),
    },
    {
        "barcode": "779000000109",
        "name": "Alcohol en gel 500 ml",
        "active_ingredient": "Alcohol etílico 70%",
        "presentation": "Botella 500 ml",
        "sale_price": Decimal("2100.00"),
        "minimum_stock": 20,
        "lots": (
            {"number": "ALC-2801", "expires_in": 620, "quantity": 90, "cost": Decimal("900.00"), "days_ago": 15},
        ),
    },
)

# Extra entries for the three medicines the original seed already created. The
# Ibuprofeno lot in the seed is expired, so this branch needs a fresh one before
# it can sell any unit.
EXTRA_LOTS: tuple[dict, ...] = (
    {
        "barcode": "779000000001",
        "number": "IBU-2702",
        "expires_in": 300,
        "quantity": 40,
        "cost": Decimal("2300.00"),
        "days_ago": 35,
    },
    {
        "barcode": "779000000002",
        "number": "PAR-2703",
        "expires_in": 240,
        "quantity": 36,
        "cost": Decimal("1600.00"),
        "days_ago": 33,
    },
    {
        "barcode": "779000000003",
        "number": "AMO-2704",
        "expires_in": 210,
        "quantity": 24,
        "cost": Decimal("3200.00"),
        "days_ago": 28,
    },
)

# (barcode, quantity, days_ago, movement type, reason)
SALES: tuple[tuple[str, int, int, MovementType, str | None], ...] = (
    ("779000000101", 6, 50, MovementType.SALE, None),
    ("779000000102", 4, 48, MovementType.SALE, None),
    ("779000000103", 8, 46, MovementType.SALE, None),
    ("779000000105", 10, 44, MovementType.SALE, None),
    ("779000000101", 5, 42, MovementType.SALE, None),
    ("779000000101", 2, 41, MovementType.WASTE, "Envase dañado en depósito"),
    ("779000000106", 6, 40, MovementType.SALE, None),
    ("779000000104", 2, 38, MovementType.SALE, None),
    ("779000000107", 2, 36, MovementType.SALE, None),
    ("779000000001", 6, 34, MovementType.SALE, None),
    ("779000000103", 7, 34, MovementType.SALE, None),
    ("779000000108", 1, 32, MovementType.SALE, None),
    ("779000000109", 12, 30, MovementType.SALE, None),
    ("779000000101", 4, 28, MovementType.SALE, None),
    ("779000000105", 12, 26, MovementType.SALE, None),
    ("779000000003", 5, 25, MovementType.SALE, None),
    ("779000000102", 5, 24, MovementType.SALE, None),
    ("779000000002", 8, 23, MovementType.SALE, None),
    ("779000000106", 7, 22, MovementType.SALE, None),
    ("779000000002", 6, 21, MovementType.SALE, None),
    ("779000000104", 3, 20, MovementType.SALE, None),
    ("779000000109", 3, 19, MovementType.WASTE, "Producto vencido"),
    ("779000000103", 9, 18, MovementType.SALE, None),
    ("779000000107", 2, 16, MovementType.SALE, None),
    ("779000000109", 15, 14, MovementType.SALE, None),
    ("779000000101", 6, 12, MovementType.SALE, None),
    ("779000000001", 5, 11, MovementType.SALE, None),
    ("779000000105", 8, 10, MovementType.SALE, None),
    ("779000000103", 1, 9, MovementType.WASTE, "Rotura durante el conteo"),
    ("779000000102", 6, 8, MovementType.SALE, None),
    ("779000000108", 2, 7, MovementType.SALE, None),
    ("779000000002", 4, 6, MovementType.SALE, None),
    ("779000000106", 5, 6, MovementType.SALE, None),
    ("779000000104", 2, 5, MovementType.SALE, None),
    ("779000000103", 6, 4, MovementType.SALE, None),
    ("779000000109", 18, 3, MovementType.SALE, None),
    ("779000000003", 4, 2, MovementType.SALE, None),
    ("779000000107", 1, 2, MovementType.SALE, None),
    ("779000000101", 3, 1, MovementType.SALE, None),
    ("779000000107", 3, 1, MovementType.SALE, None),
)

BUSINESS_HOURS = (9, 10, 11, 12, 14, 15, 16, 17, 18)


def demo_lot_numbers() -> set[str]:
    numbers = {lot["number"] for item in CATALOG for lot in item["lots"]}
    numbers.update(lot["number"] for lot in EXTRA_LOTS)
    return numbers


def _medicine_by_barcode(db: Session, barcode: str) -> Medicine | None:
    return db.scalar(select(Medicine).where(Medicine.barcode == barcode))


def _ensure_medicine(db: Session, item: dict) -> Medicine:
    medicine = _medicine_by_barcode(db, item["barcode"])
    if medicine is not None:
        return medicine
    medicine = Medicine(
        barcode=item["barcode"],
        name=item["name"],
        active_ingredient=item["active_ingredient"],
        presentation=item["presentation"],
        sale_price=item["sale_price"],
        minimum_stock=item["minimum_stock"],
    )
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine


def _lot_exists(db: Session, medicine_id: int, branch_id: int, lot_number: str) -> bool:
    return (
        db.scalar(
            select(Lot.id).where(
                Lot.medicine_id == medicine_id,
                Lot.branch_id == branch_id,
                Lot.lot_number == lot_number,
            )
        )
        is not None
    )


def _stamp(index: int, days_ago: int) -> datetime:
    hour = BUSINESS_HOURS[index % len(BUSINESS_HOURS)]
    minute = (index * 7) % 60
    day = date.today() - timedelta(days=days_ago)
    return datetime.combine(day, time(hour, minute), tzinfo=timezone.utc)


def _available_stock(db: Session, medicine_id: int, branch_id: int, include_expired: bool) -> int:
    conditions = [
        Lot.medicine_id == medicine_id,
        Lot.branch_id == branch_id,
        Lot.current_quantity > 0,
    ]
    if not include_expired:
        conditions.append(Lot.expiration_date >= date.today())
    total = db.scalar(select(func.coalesce(func.sum(Lot.current_quantity), 0)).where(*conditions))
    return int(total or 0)


def seed(db: Session) -> dict[str, int]:
    created = {"medicines": 0, "entries": 0, "sales": 0, "waste": 0, "alerts": 0, "backdated": 0}

    users = list(db.scalars(select(User).where(User.active.is_(True)).order_by(User.id)))
    if not users:
        raise SystemExit("No active users found; run `python -m scripts.seed` first.")
    admin = users[0]
    employee = users[1] if len(users) > 1 else users[0]
    supplier = db.scalar(select(Supplier).order_by(Supplier.id))

    # Medicines first so every barcode resolves during the timeline pass.
    before = {medicine.barcode for medicine in db.scalars(select(Medicine))}
    for item in CATALOG:
        _ensure_medicine(db, item)
    after = {medicine.barcode for medicine in db.scalars(select(Medicine))}
    created["medicines"] = len(after - before)

    operations: list[dict] = []
    for item in CATALOG:
        for lot in item["lots"]:
            operations.append({"kind": "entry", "barcode": item["barcode"], **lot})
    for lot in EXTRA_LOTS:
        operations.append({"kind": "entry", "barcode": lot["barcode"], **lot})
    for barcode, quantity, days_ago, movement_type, reason in SALES:
        operations.append(
            {
                "kind": "sale",
                "barcode": barcode,
                "quantity": quantity,
                "days_ago": days_ago,
                "movement_type": movement_type,
                "reason": reason,
            }
        )

    # Oldest first. Entries win ties so a sale always has stock available.
    operations.sort(key=lambda op: (-op["days_ago"], op["kind"] != "entry"))

    timeline: list[tuple[Movement, int]] = []
    order = 0
    for op in operations:
        medicine = _medicine_by_barcode(db, op["barcode"])
        if medicine is None:
            continue
        actor = admin if order % 2 == 0 else employee

        if op["kind"] == "entry":
            if _lot_exists(db, medicine.id, actor.branch_id, op["number"]):
                continue
            movement = inventory_service.register_entry(
                db,
                actor,
                EntryRequest(
                    medicine_id=medicine.id,
                    lot_number=op["number"],
                    expiration_date=date.today() + timedelta(days=op["expires_in"]),
                    quantity=op["quantity"],
                    unit_cost=op["cost"],
                    supplier_id=supplier.id if supplier is not None else None,
                    reason="Reposición de stock",
                ),
            )
            created["entries"] += 1
            timeline.append((movement, op["days_ago"]))
        else:
            is_waste = op["movement_type"] is MovementType.WASTE
            if _available_stock(db, medicine.id, actor.branch_id, is_waste) < op["quantity"]:
                continue
            movements = inventory_service.register_sale(
                db,
                actor,
                SaleRequest(
                    medicine_id=medicine.id,
                    quantity=op["quantity"],
                    movement_type=op["movement_type"],
                    reason=op["reason"],
                ),
            )
            key = "waste" if op["movement_type"] is MovementType.WASTE else "sales"
            created[key] += 1
            for movement in movements:
                timeline.append((movement, op["days_ago"]))
        order += 1

    # Backdate in creation order so kardex balances stay monotonic.
    for index, (movement, days_ago) in enumerate(timeline):
        db.execute(
            update(Movement)
            .where(Movement.id == movement.id)
            .values(created_at=_stamp(index, days_ago))
        )
        created["backdated"] += 1
    db.commit()

    created.update(_reconcile_lots(db, admin))
    created["alerts"] = alert_service.generate_alerts(db, branch_id=admin.branch_id)
    return created


def _reconcile_lots(db: Session, actor: User) -> dict[str, int]:
    """Make every lot readable as a coherent timeline.

    The original ``scripts.seed`` creates lots without an ENTRY movement, so the
    kardex shows sales against a balance that nothing explains. This pass adds
    the missing initial entry and replays every lot in chronological order so
    ``lot_balance`` always matches the sum of the previous movements.
    """
    stats = {"entries_added": 0, "balances_fixed": 0}

    for lot in db.scalars(select(Lot).where(Lot.branch_id == actor.branch_id)):
        movements = list(db.scalars(select(Movement).where(Movement.lot_id == lot.id)))
        entries = [m for m in movements if m.movement_type is MovementType.ENTRY]
        outs = sorted(
            (m for m in movements if m.movement_type is not MovementType.ENTRY),
            key=lambda m: m.created_at,
        )
        if len(entries) > 1:
            # Not produced by this script; leave the lot untouched.
            continue

        initial = lot.current_quantity + sum(m.quantity for m in outs)

        if entries:
            entry = entries[0]
            if entry.quantity != initial:
                entry.quantity = initial
                entry.lot_balance = initial
                stats["balances_fixed"] += 1
        else:
            first = outs[0].created_at if outs else datetime.now(timezone.utc)
            db.add(
                Movement(
                    lot_id=lot.id,
                    user_id=actor.id,
                    movement_type=MovementType.ENTRY,
                    quantity=initial,
                    lot_balance=initial,
                    unit_cost=lot.unit_cost,
                    reason="Carga inicial de inventario",
                    created_at=first - timedelta(days=20),
                )
            )
            stats["entries_added"] += 1

        running = initial
        for movement in outs:
            running -= movement.quantity
            if movement.lot_balance != running:
                movement.lot_balance = running
                stats["balances_fixed"] += 1

    db.commit()
    return stats


def clean(db: Session) -> dict[str, int]:
    removed = {"medicines": 0, "lots": 0, "movements": 0, "alerts": 0}

    medicine_ids = list(
        db.scalars(select(Medicine.id).where(Medicine.barcode.like(f"{DEMO_BARCODE_PREFIX}%")))
    )
    lot_ids = list(
        db.scalars(
            select(Lot.id).where(
                (Lot.medicine_id.in_(medicine_ids)) | (Lot.lot_number.in_(demo_lot_numbers()))
            )
        )
    )

    if lot_ids:
        removed["alerts"] = db.execute(delete(Alert).where(Alert.lot_id.in_(lot_ids))).rowcount or 0
        removed["movements"] = (
            db.execute(delete(Movement).where(Movement.lot_id.in_(lot_ids))).rowcount or 0
        )
        removed["lots"] = db.execute(delete(Lot).where(Lot.id.in_(lot_ids))).rowcount or 0
    if medicine_ids:
        removed["medicines"] = (
            db.execute(delete(Medicine).where(Medicine.id.in_(medicine_ids))).rowcount or 0
        )

    db.commit()
    return removed


def demo_already_applied(db: Session) -> bool:
    count = db.scalar(
        select(func.count(Movement.id)).where(
            Movement.lot_id.in_(
                select(Lot.id).where(Lot.lot_number.in_(demo_lot_numbers()))
            )
        )
    )
    return bool(count)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--clean",
        action="store_true",
        help="remove the demo medicines and demo lots instead of inserting them",
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="only rebuild the initial entries and lot balances; inserts nothing",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.clean:
            result = clean(db)
            print("Clean:", result)
            return
        if args.reconcile:
            admin = db.scalars(select(User).where(User.active.is_(True)).order_by(User.id)).first()
            if admin is None:
                raise SystemExit("No active users found.")
            result = _reconcile_lots(db, admin)
            result["alerts"] = alert_service.generate_alerts(db, branch_id=admin.branch_id)
            print("Reconcile:", result)
            return
        if demo_already_applied(db):
            raise SystemExit(
                "Demo data is already in the database. Nothing was inserted.\n"
                "Use --reconcile to rebuild lot balances, or --clean to remove it."
            )
        result = seed(db)
    print("Demo data:", result)


if __name__ == "__main__":
    main()
