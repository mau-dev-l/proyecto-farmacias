from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models import Alert, Lot, Medicine, Movement, User
from app.models.entities import AlertType, MovementType
from app.schemas.alerts import DashboardResponse, ExpiringLotResponse, InventoryReportResponse

router = APIRouter(prefix="/reportes", tags=["reports"])


@router.get("/proximos-vencer", response_model=list[ExpiringLotResponse])
def expiring_lots(
    days: int = Query(default=30, ge=0, le=365),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[ExpiringLotResponse]:
    remaining = (Lot.expiration_date - date.today()).label("days_remaining")
    query = (
        select(Lot.id, Medicine.name, Lot.lot_number, Lot.expiration_date, remaining, Lot.current_quantity, (Lot.current_quantity * Lot.unit_cost).label("risk_value"))
        .join(Medicine, Lot.medicine_id == Medicine.id)
        .where(Lot.branch_id == current_user.branch_id, Lot.current_quantity > 0, Lot.expiration_date.between(date.today(), date.today() + timedelta(days=days)))
        .order_by(Lot.expiration_date)
    )
    return [ExpiringLotResponse(lot_id=row.id, medicine_name=row.name, lot_number=row.lot_number, expiration_date=row.expiration_date, days_remaining=row.days_remaining, quantity=row.current_quantity, risk_value=row.risk_value) for row in db.execute(query)]


@router.get("/mermas")
def waste_report(
    desde: date | None = None,
    hasta: date | None = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Decimal | int]:
    query = select(func.coalesce(func.sum(Movement.quantity * Movement.unit_cost), 0), func.coalesce(func.sum(Movement.quantity), 0)).join(Lot, Movement.lot_id == Lot.id).where(Lot.branch_id == current_user.branch_id, Movement.movement_type == MovementType.WASTE)
    if desde:
        query = query.where(Movement.created_at >= desde)
    if hasta:
        query = query.where(Movement.created_at < hasta + timedelta(days=1))
    value, quantity = db.execute(query).one()
    return {"quantity": quantity, "total_value": value}


@router.get("/inventario", response_model=InventoryReportResponse)
def inventory_report(current_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> InventoryReportResponse:
    total_units, total_value, medicine_count = db.execute(select(func.coalesce(func.sum(Lot.current_quantity), 0), func.coalesce(func.sum(Lot.current_quantity * Lot.unit_cost), 0), func.count(func.distinct(Lot.medicine_id))).where(Lot.branch_id == current_user.branch_id, Lot.current_quantity > 0)).one()
    return InventoryReportResponse(total_units=total_units, total_value=total_value, medicine_count=medicine_count)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(current_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> DashboardResponse:
    report = inventory_report(current_user, db)
    unread = db.scalar(select(func.count(Alert.id)).join(Lot, Alert.lot_id == Lot.id).where(Lot.branch_id == current_user.branch_id, Alert.read.is_(False))) or 0
    expiring = db.scalar(select(func.count(Lot.id)).where(Lot.branch_id == current_user.branch_id, Lot.current_quantity > 0, Lot.expiration_date.between(date.today(), date.today() + timedelta(days=30)))) or 0
    return DashboardResponse(**report.model_dump(), unread_alerts=unread, expiring_lots=expiring)
