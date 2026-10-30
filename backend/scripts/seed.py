"""Idempotent development seed data.

Run from the backend directory with the database available:

    python -m scripts.seed
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import AlertConfiguration, Branch, Lot, Medicine, Supplier, User
from app.models.entities import LotStatus, UserRole


def get_or_create(db: Session, model, defaults: dict | None = None, **filters):
    instance = db.scalar(select(model).filter_by(**filters))
    if instance is not None:
        return instance, False
    instance = model(**filters, **(defaults or {}))
    db.add(instance)
    db.flush()
    return instance, True


def seed(db: Session) -> dict[str, int]:
    created = {"branches": 0, "users": 0, "suppliers": 0, "medicines": 0, "lots": 0}

    branch, was_created = get_or_create(
        db,
        Branch,
        name="Sucursal Central",
        defaults={"address": "Av. Principal 123"},
    )
    created["branches"] += int(was_created)

    for email, name, role in (
        ("admin@farmacia.com", "Administrador", UserRole.ADMIN),
        ("empleado@farmacia.com", "Empleado de Mostrador", UserRole.EMPLOYEE),
    ):
        _, was_created = get_or_create(
            db,
            User,
            email=email,
            defaults={
                "branch_id": branch.id,
                "name": name,
                "password_hash": hash_password("Farmacia123"),
                "role": role,
            },
        )
        created["users"] += int(was_created)

    supplier, was_created = get_or_create(
        db,
        Supplier,
        name="Droguería del Sur",
        defaults={"phone": "11-5555-0101"},
    )
    created["suppliers"] += int(was_created)

    catalog = (
        {
            "barcode": "779000000001",
            "name": "Ibuprofeno 400 mg",
            "active_ingredient": "Ibuprofeno",
            "presentation": "Caja x 20 comprimidos",
            "sale_price": Decimal("4500.00"),
            "minimum_stock": 10,
            "lot_number": "IBU-2601",
            "expiration_date": date.today() + timedelta(days=10),
            "quantity": 24,
            "unit_cost": Decimal("2200.00"),
        },
        {
            "barcode": "779000000002",
            "name": "Paracetamol 500 mg",
            "active_ingredient": "Paracetamol",
            "presentation": "Caja x 10 comprimidos",
            "sale_price": Decimal("3200.50"),
            "minimum_stock": 12,
            "lot_number": "PAR-2602",
            "expiration_date": date.today() + timedelta(days=75),
            "quantity": 40,
            "unit_cost": Decimal("1500.00"),
        },
        {
            "barcode": "779000000003",
            "name": "Amoxicilina 500 mg",
            "active_ingredient": "Amoxicilina",
            "presentation": "Caja x 12 cápsulas",
            "sale_price": Decimal("5800.00"),
            "minimum_stock": 8,
            "lot_number": "AMO-2603",
            "expiration_date": date.today() + timedelta(days=200),
            "quantity": 18,
            "unit_cost": Decimal("3100.00"),
        },
    )

    for item in catalog:
        medicine, was_created = get_or_create(
            db,
            Medicine,
            barcode=item["barcode"],
            defaults={
                "name": item["name"],
                "active_ingredient": item["active_ingredient"],
                "presentation": item["presentation"],
                "sale_price": item["sale_price"],
                "minimum_stock": item["minimum_stock"],
            },
        )
        created["medicines"] += int(was_created)

        _, was_created = get_or_create(
            db,
            Lot,
            medicine_id=medicine.id,
            branch_id=branch.id,
            lot_number=item["lot_number"],
            defaults={
                "supplier_id": supplier.id,
                "expiration_date": item["expiration_date"],
                "current_quantity": item["quantity"],
                "unit_cost": item["unit_cost"],
                "status": LotStatus.ACTIVE,
            },
        )
        created["lots"] += int(was_created)

    for threshold in (90, 60, 30):
        _, was_created = get_or_create(
            db,
            AlertConfiguration,
            branch_id=branch.id,
            lead_days=threshold,
        )
        created["alert_thresholds"] = created.get("alert_thresholds", 0) + int(was_created)

    db.commit()
    return created


def main() -> None:
    with SessionLocal() as db:
        created = seed(db)
    print("Seed completed:", created)


if __name__ == "__main__":
    main()
