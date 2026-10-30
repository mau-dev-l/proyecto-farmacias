from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import Medicine, User
from app.schemas.medicines import BarcodeLookupResponse, MedicineCreate, MedicineResponse, MedicineUpdate
from app.services import catalog_service

router = APIRouter(prefix="/medicamentos", tags=["medicines"])


@router.get("", response_model=list[MedicineResponse])
def list_medicines(
    response: Response,
    q: str | None = Query(default=None, min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Medicine]:
    response.headers["X-Total-Count"] = str(catalog_service.count_medicines(db, q))
    return catalog_service.list_medicines(db, q, page, page_size)


@router.get("/barcode/{barcode}", response_model=BarcodeLookupResponse)
def get_by_barcode(
    barcode: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BarcodeLookupResponse:
    return catalog_service.lookup_barcode(db, current_user.branch_id, barcode)


@router.post("", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
def create_medicine(
    payload: MedicineCreate,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Medicine:
    return catalog_service.create_medicine(db, payload)


@router.put("/{medicine_id}", response_model=MedicineResponse)
def update_medicine(
    medicine_id: int,
    payload: MedicineUpdate,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Medicine:
    return catalog_service.update_medicine(db, medicine_id, payload)


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_medicine(
    medicine_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    catalog_service.deactivate_medicine(db, medicine_id)
