from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models import Branch, User
from app.schemas.admin import BranchCreate, BranchResponse, BranchUpdate, UserCreate, UserUpdate
from app.schemas.auth import UserResponse
from app.services import admin_service

router = APIRouter(tags=["administration"])


@router.get("/sucursales", response_model=list[BranchResponse])
def list_branches(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Branch]:
    return admin_service.list_branches(db)


@router.post("/sucursales", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(
    payload: BranchCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Branch:
    return admin_service.create_branch(db, payload)


@router.put("/sucursales/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: int,
    payload: BranchUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Branch:
    return admin_service.update_branch(db, branch_id, payload)


@router.get("/usuarios", response_model=list[UserResponse])
def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[User]:
    return admin_service.list_users(db)


@router.post("/usuarios", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    return admin_service.create_user(db, payload)


@router.put("/usuarios/{user_id}", response_model=UserResponse)
@router.patch("/usuarios/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    return admin_service.update_user(db, current_user, user_id, payload)
