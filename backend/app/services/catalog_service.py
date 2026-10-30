from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Medicine
from app.models.entities import LotStatus
from app.repositories import lots as lots_repository
from app.repositories import medicines as medicines_repository
from app.schemas.inventory import LotResponse
from app.schemas.medicines import BarcodeLookupResponse, MedicineCreate, MedicineUpdate


def list_medicines(db: Session, q: str | None, page: int, page_size: int) -> list[Medicine]:
    return medicines_repository.list_active(db, q, page, page_size)


def count_medicines(db: Session, q: str | None) -> int:
    return medicines_repository.count_active(db, q)


def get_by_barcode(db: Session, barcode: str) -> Medicine:
    medicine = medicines_repository.get_active_by_barcode(db, barcode)
    if medicine is None:
        raise NotFoundError("Medicine not found")
    return medicine


def lookup_barcode(db: Session, branch_id: int, barcode: str) -> BarcodeLookupResponse:
    medicine = get_by_barcode(db, barcode)
    lots = [
        lot
        for lot in lots_repository.list_for_medicine(db, medicine.id, branch_id)
        if lot.current_quantity > 0 and lot.status == LotStatus.ACTIVE
    ]
    return BarcodeLookupResponse(
        id=medicine.id,
        barcode=medicine.barcode,
        name=medicine.name,
        active_ingredient=medicine.active_ingredient,
        presentation=medicine.presentation,
        sale_price=medicine.sale_price,
        minimum_stock=medicine.minimum_stock,
        active=medicine.active,
        total_stock=sum(lot.current_quantity for lot in lots),
        lots=[LotResponse.model_validate(lot) for lot in lots],
    )


def create_medicine(db: Session, payload: MedicineCreate) -> Medicine:
    medicine = Medicine(**payload.model_dump())
    medicines_repository.add(db, medicine)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ConflictError("Barcode already exists") from error
    db.refresh(medicine)
    return medicine


def update_medicine(db: Session, medicine_id: int, payload: MedicineUpdate) -> Medicine:
    medicine = medicines_repository.get(db, medicine_id)
    if medicine is None:
        raise NotFoundError("Medicine not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(medicine, field, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ConflictError("Barcode already exists") from error
    db.refresh(medicine)
    return medicine


def deactivate_medicine(db: Session, medicine_id: int) -> None:
    medicine = medicines_repository.get(db, medicine_id)
    if medicine is None:
        raise NotFoundError("Medicine not found")
    medicine.active = False
    db.commit()
