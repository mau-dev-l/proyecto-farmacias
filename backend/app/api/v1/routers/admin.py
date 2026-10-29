from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.security import hash_password
from app.models import Branch, User
from app.schemas.admin import BranchCreate, BranchResponse, BranchUpdate, UserCreate, UserUpdate
from app.schemas.auth import UserResponse

router = APIRouter(tags=["administration"])


@router.get("/sucursales", response_model=list[BranchResponse])
def list_branches(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[Branch]:
    return list(db.scalars(select(Branch).order_by(Branch.name)))


@router.post("/sucursales", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(payload: BranchCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> Branch:
    branch = Branch(**payload.model_dump())
    db.add(branch)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Branch name already exists") from error
    db.refresh(branch)
    return branch


@router.put("/sucursales/{branch_id}", response_model=BranchResponse)
def update_branch(branch_id: int, payload: BranchUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> Branch:
    branch = db.get(Branch, branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(branch, field, value)
    db.commit()
    db.refresh(branch)
    return branch


@router.get("/usuarios", response_model=list[UserResponse])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.name)))


@router.post("/usuarios", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> User:
    if db.get(Branch, payload.branch_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    user = User(**payload.model_dump(exclude={"password"}), password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists") from error
    db.refresh(user)
    return user


@router.patch("/usuarios/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    values = payload.model_dump(exclude_unset=True, exclude={"password"})
    for field, value in values.items():
        setattr(user, field, value)
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return user
