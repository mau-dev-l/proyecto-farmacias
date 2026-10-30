from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Alert, Lot, Medicine, Movement
from app.models.entities import MovementType


def inventory_summary(db: Session, branch_id: int) -> tuple[int, Decimal, int]:
    return db.execute(
        select(
            func.coalesce(func.sum(Lot.current_quantity), 0),
            func.coalesce(func.sum(Lot.current_quantity * Lot.unit_cost), 0),
            func.count(func.distinct(Lot.medicine_id)),
        ).where(Lot.branch_id == branch_id, Lot.current_quantity > 0)
    ).one()


def expiring_lots(db: Session, branch_id: int, days: int) -> list:
    return list(
        db.execute(
            select(
                Lot.id.label("lot_id"),
                Medicine.name.label("medicine_name"),
                Lot.lot_number,
                Lot.expiration_date,
                Lot.current_quantity,
                (Lot.current_quantity * Lot.unit_cost).label("risk_value"),
            )
            .join(Medicine, Lot.medicine_id == Medicine.id)
            .where(
                Lot.branch_id == branch_id,
                Lot.current_quantity > 0,
                Lot.expiration_date.between(date.today(), date.today() + timedelta(days=days)),
            )
            .order_by(Lot.expiration_date)
        )
    )


def waste_summary(
    db: Session,
    branch_id: int,
    desde: date | None = None,
    hasta: date | None = None,
) -> tuple[Decimal, int]:
    query = (
        select(
            func.coalesce(func.sum(Movement.quantity * Movement.unit_cost), 0),
            func.coalesce(func.sum(Movement.quantity), 0),
        )
        .join(Lot, Movement.lot_id == Lot.id)
        .where(Lot.branch_id == branch_id, Movement.movement_type == MovementType.WASTE)
    )
    if desde is not None:
        query = query.where(Movement.created_at >= datetime.combine(desde, time.min))
    if hasta is not None:
        query = query.where(Movement.created_at < datetime.combine(hasta + timedelta(days=1), time.min))
    return db.execute(query).one()


def waste_by_medicine(
    db: Session,
    branch_id: int,
    desde: date | None = None,
    hasta: date | None = None,
) -> list:
    total_value = func.coalesce(func.sum(Movement.quantity * Movement.unit_cost), 0).label(
        "total_value"
    )
    query = (
        select(
            Medicine.name.label("medicine_name"),
            func.coalesce(func.sum(Movement.quantity), 0).label("quantity"),
            total_value,
        )
        .join(Lot, Movement.lot_id == Lot.id)
        .join(Medicine, Lot.medicine_id == Medicine.id)
        .where(Lot.branch_id == branch_id, Movement.movement_type == MovementType.WASTE)
        .group_by(Medicine.name)
        .order_by(total_value.desc())
    )
    if desde is not None:
        query = query.where(Movement.created_at >= datetime.combine(desde, time.min))
    if hasta is not None:
        query = query.where(Movement.created_at < datetime.combine(hasta + timedelta(days=1), time.min))
    return list(db.execute(query))


def unread_alert_count(db: Session, branch_id: int) -> int:
    return db.scalar(
        select(func.count(Alert.id))
        .join(Lot, Alert.lot_id == Lot.id)
        .where(Lot.branch_id == branch_id, Alert.read.is_(False))
    ) or 0


def expiring_lot_count(db: Session, branch_id: int, days: int) -> int:
    return db.scalar(
        select(func.count(Lot.id)).where(
            Lot.branch_id == branch_id,
            Lot.current_quantity > 0,
            Lot.expiration_date.between(date.today(), date.today() + timedelta(days=days)),
        )
    ) or 0
