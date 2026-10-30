from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lot
from app.models.entities import LotStatus


def get(db: Session, lot_id: int) -> Lot | None:
    return db.get(Lot, lot_id)


def get_for_update(db: Session, lot_id: int) -> Lot | None:
    return db.scalar(select(Lot).where(Lot.id == lot_id).with_for_update())


def get_by_number(db: Session, medicine_id: int, branch_id: int, lot_number: str) -> Lot | None:
    return db.scalar(
        select(Lot).where(
            Lot.medicine_id == medicine_id,
            Lot.branch_id == branch_id,
            Lot.lot_number == lot_number,
        )
    )


def list_for_medicine(db: Session, medicine_id: int, branch_id: int) -> list[Lot]:
    return list(
        db.scalars(
            select(Lot)
            .where(Lot.medicine_id == medicine_id, Lot.branch_id == branch_id)
            .order_by(Lot.expiration_date, Lot.id)
        )
    )


def list_active_for_branch(db: Session, branch_id: int) -> list[Lot]:
    return list(
        db.scalars(
            select(Lot)
            .where(
                Lot.branch_id == branch_id,
                Lot.status == LotStatus.ACTIVE,
                Lot.current_quantity > 0,
            )
            .order_by(Lot.expiration_date, Lot.id)
        )
    )


def list_fefo(
    db: Session,
    medicine_id: int,
    branch_id: int,
    *,
    include_expired: bool = False,
    lock: bool = False,
) -> list[Lot]:
    query = select(Lot).where(
        Lot.medicine_id == medicine_id,
        Lot.branch_id == branch_id,
        Lot.current_quantity > 0,
    )
    if not include_expired:
        query = query.where(Lot.expiration_date >= date.today())
    query = query.order_by(Lot.expiration_date, Lot.id)
    if lock:
        query = query.with_for_update()
    return list(db.scalars(query))


def list_all_active_with_stock(db: Session) -> list[Lot]:
    return list(
        db.scalars(
            select(Lot)
            .where(Lot.status == LotStatus.ACTIVE, Lot.current_quantity > 0)
            .order_by(Lot.expiration_date, Lot.id)
        )
    )


def add(db: Session, lot: Lot) -> Lot:
    db.add(lot)
    db.flush()
    return lot
