from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import verify_password
from app.models import User
from app.repositories import users as users_repository


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _is_locked(user: User) -> bool:
    return user.locked_until is not None and _as_utc(user.locked_until) > _utc_now()


def authenticate(db: Session, email: str, password: str) -> User:
    user = users_repository.get_by_email(db, email)
    if user is None:
        raise AuthenticationError("Invalid credentials")
    if _is_locked(user):
        raise AuthenticationError("Account temporarily locked")
    if not verify_password(password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= settings.max_failed_attempts:
            user.locked_until = _utc_now() + timedelta(minutes=settings.lockout_minutes)
            user.failed_attempts = 0
        db.commit()
        raise AuthenticationError("Invalid credentials")
    if not user.active:
        raise AuthenticationError("Inactive user")
    if user.failed_attempts or user.locked_until is not None:
        user.failed_attempts = 0
        user.locked_until = None
        db.commit()
    return user
