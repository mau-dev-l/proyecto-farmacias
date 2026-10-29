from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import Medicine, User
from app.schemas.medicines import MedicineCreate, MedicineResponse, MedicineUpdate

router = APIRouter(prefix="/medicamentos", tags=["medicines"])


@router.get("", response_model=list[MedicineResponse])
def list_medicines(
    q: str | None = Query(default=None, min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Medicine]:
    query = select(Medicine).where(Medicine.active.is_(True)).order_by(Medicine.name)
    if q:
        query = query.where(Medicine.name.ilike(f"%{q}%"))
    return list(db.scalars(query.offset((page - 1) * page_size).limit(page_size)))


@router.get("/barcode/{barcode}", response_model=MedicineResponse)
def get_by_barcode(barcode: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Medicine:
    medicine = db.scalar(select(Medicine).where(Medicine.barcode == barcode, Medicine.active.is_(True)))
    if medicine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    return medicine


@router.post("", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
def create_medicine(payload: MedicineCreate, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Medicine:
    medicine = Medicine(**payload.model_dump())
    db.add(medicine)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Barcode already exists") from error
    db.refresh(medicine)
    return medicine


@router.put("/{medicine_id}", response_model=MedicineResponse)
def update_medicine(
    medicine_id: int,
    payload: MedicineUpdate,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Medicine:
    medicine = db.get(Medicine, medicine_id)
    if medicine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(medicine, field, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Barcode already exists") from error
    db.refresh(medicine)
    return medicine


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_medicine(medicine_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> None:
    medicine = db.get(Medicine, medicine_id)
    if medicine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    medicine.active = False
    db.commit()
