from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models import User
from app.schemas.alerts import (
    DashboardResponse,
    ExpiringLotResponse,
    InventoryReportResponse,
    WasteReportResponse,
)
from app.schemas.inventory import KardexEntry
from app.services import report_service

router = APIRouter(prefix="/reportes", tags=["reports"])

ReportType = Literal["mermas", "proximos-vencer", "inventario", "movimientos"]


@router.get("/proximos-vencer", response_model=list[ExpiringLotResponse])
def expiring_lots(
    days: int = Query(default=30, ge=0, le=365),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[ExpiringLotResponse]:
    return report_service.expiring_lots(db, current_user, days)


@router.get("/mermas", response_model=WasteReportResponse)
def waste_report(
    desde: date | None = None,
    hasta: date | None = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WasteReportResponse:
    return report_service.waste_report(db, current_user, desde, hasta)


@router.get("/inventario", response_model=InventoryReportResponse)
def inventory_report(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> InventoryReportResponse:
    return report_service.inventory_report(db, current_user)


@router.get("/movimientos", response_model=list[KardexEntry])
def movements_report(
    desde: date | None = None,
    hasta: date | None = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[KardexEntry]:
    return report_service.movements_report(db, current_user, desde, hasta)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    return report_service.dashboard(db, current_user)


@router.get("/exportar")
def export_report(
    tipo: ReportType,
    desde: date | None = None,
    hasta: date | None = None,
    days: int = Query(default=30, ge=0, le=365),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    filename, content = report_service.export_csv(
        db,
        current_user,
        tipo,
        desde,
        hasta,
        days,
    )
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
