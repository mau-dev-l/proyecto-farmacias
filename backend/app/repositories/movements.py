from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lot, Movement, User


def list_kardex(
    db: Session,
    branch_id: int,
    medicine_id: int | None = None,
    lot_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> list:
    query = (
        select(
            Movement.id,
            Movement.lot_id,
            Movement.user_id,
            Movement.movement_type,
            Movement.quantity,
            Movement.lot_balance,
            Movement.unit_cost,
            Movement.reason,
            Movement.created_at,
            Lot.lot_number,
            User.name.label("user_name"),
        )
        .join(Lot, Movement.lot_id == Lot.id)
        .join(User, Movement.user_id == User.id)
        .where(Lot.branch_id == branch_id)
        .order_by(Movement.created_at.desc())
    )
    if medicine_id is not None:
        query = query.where(Lot.medicine_id == medicine_id)
    if lot_id is not None:
        query = query.where(Movement.lot_id == lot_id)
    if desde is not None:
        query = query.where(Movement.created_at >= datetime.combine(desde, time.min))
    if hasta is not None:
        query = query.where(Movement.created_at < datetime.combine(hasta + timedelta(days=1), time.min))
    return list(db.execute(query))


def add(db: Session, movement: Movement) -> Movement:
    db.add(movement)
    return movement
