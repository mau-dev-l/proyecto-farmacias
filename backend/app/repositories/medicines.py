from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Lot, Medicine
from app.models.entities import LotStatus


def get(db: Session, medicine_id: int) -> Medicine | None:
    return db.get(Medicine, medicine_id)


def get_active_by_barcode(db: Session, barcode: str) -> Medicine | None:
    return db.scalar(select(Medicine).where(Medicine.barcode == barcode, Medicine.active.is_(True)))


def _search_filter(q: str):
    pattern = f"%{q}%"
    return or_(Medicine.name.ilike(pattern), Medicine.barcode.ilike(pattern))


def list_active(db: Session, q: str | None, page: int, page_size: int) -> list[Medicine]:
    query = select(Medicine).where(Medicine.active.is_(True)).order_by(Medicine.name)
    if q:
        query = query.where(_search_filter(q))
    return list(db.scalars(query.offset((page - 1) * page_size).limit(page_size)))


def count_active(db: Session, q: str | None) -> int:
    query = select(func.count(Medicine.id)).where(Medicine.active.is_(True))
    if q:
        query = query.where(_search_filter(q))
    return db.scalar(query) or 0


def list_stock_by_branch(db: Session, branch_id: int, q: str | None = None) -> list:
    total_stock = func.coalesce(func.sum(Lot.current_quantity), 0).label("total_stock")
    query = (
        select(
            Medicine.id.label("medicine_id"),
            Medicine.name,
            Medicine.barcode,
            Medicine.minimum_stock,
            total_stock,
        )
        .outerjoin(
            Lot,
            (Lot.medicine_id == Medicine.id)
            & (Lot.branch_id == branch_id)
            & (Lot.status == LotStatus.ACTIVE),
        )
        .where(Medicine.active.is_(True))
        .group_by(Medicine.id)
        .order_by(Medicine.name)
    )
    if q:
        query = query.where(_search_filter(q))
    return list(db.execute(query))


def add(db: Session, medicine: Medicine) -> Medicine:
    db.add(medicine)
    return medicine
