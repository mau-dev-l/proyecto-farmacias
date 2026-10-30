from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Branch


def get(db: Session, branch_id: int) -> Branch | None:
    return db.get(Branch, branch_id)


def list_all(db: Session) -> list[Branch]:
    return list(db.scalars(select(Branch).order_by(Branch.name)))


def add(db: Session, branch: Branch) -> Branch:
    db.add(branch)
    return branch
