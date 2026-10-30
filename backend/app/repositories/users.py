from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def get(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def list_all(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.name)))


def add(db: Session, user: User) -> User:
    db.add(user)
    return user
