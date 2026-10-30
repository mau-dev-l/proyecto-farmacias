from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models import Branch, User
from app.repositories import branches as branches_repository
from app.repositories import users as users_repository
from app.schemas.admin import BranchCreate, BranchUpdate, UserCreate, UserUpdate


def list_branches(db: Session) -> list[Branch]:
    return branches_repository.list_all(db)


def create_branch(db: Session, payload: BranchCreate) -> Branch:
    branch = Branch(**payload.model_dump())
    branches_repository.add(db, branch)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ConflictError("Branch name already exists") from error
    db.refresh(branch)
    return branch


def update_branch(db: Session, branch_id: int, payload: BranchUpdate) -> Branch:
    branch = branches_repository.get(db, branch_id)
    if branch is None:
        raise NotFoundError("Branch not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(branch, field, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ConflictError("Branch name already exists") from error
    db.refresh(branch)
    return branch


def list_users(db: Session) -> list[User]:
    return users_repository.list_all(db)


def create_user(db: Session, payload: UserCreate) -> User:
    if branches_repository.get(db, payload.branch_id) is None:
        raise NotFoundError("Branch not found")
    values = payload.model_dump(exclude={"password"})
    values["email"] = values["email"].lower()
    user = User(**values, password_hash=hash_password(payload.password))
    users_repository.add(db, user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ConflictError("Email already exists") from error
    db.refresh(user)
    return user


def update_user(db: Session, current_user: User, user_id: int, payload: UserUpdate) -> User:
    user = users_repository.get(db, user_id)
    if user is None:
        raise NotFoundError("User not found")
    if user.id == current_user.id and payload.role is not None and payload.role.value != "ADMIN":
        raise BusinessRuleError("Administrators cannot remove their own admin role")
    values = payload.model_dump(exclude_unset=True, exclude={"password"})
    if "branch_id" in values and branches_repository.get(db, values["branch_id"]) is None:
        raise NotFoundError("Branch not found")
    if "email" in values:
        values["email"] = values["email"].lower()
    for field, value in values.items():
        setattr(user, field, value)
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ConflictError("Email already exists") from error
    db.refresh(user)
    return user
