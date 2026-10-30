import csv
import io
from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.models import User
from app.repositories import reports as reports_repository
from app.schemas.alerts import (
    DashboardResponse,
    ExpiringLotResponse,
    InventoryReportResponse,
    WasteItem,
    WasteReportResponse,
)
from app.schemas.inventory import KardexEntry
from app.services import inventory_service


def _validate_range(desde: date | None, hasta: date | None) -> None:
    if desde is not None and hasta is not None and hasta < desde:
        raise BusinessRuleError("End date cannot be earlier than start date")


def expiring_lots(db: Session, current_user: User, days: int) -> list[ExpiringLotResponse]:
    today = date.today()
    return [
        ExpiringLotResponse(
            lot_id=row.lot_id,
            medicine_name=row.medicine_name,
            lot_number=row.lot_number,
            expiration_date=row.expiration_date,
            days_remaining=(row.expiration_date - today).days,
            quantity=row.current_quantity,
            risk_value=row.risk_value,
        )
        for row in reports_repository.expiring_lots(db, current_user.branch_id, days)
    ]


def waste_report(
    db: Session,
    current_user: User,
    desde: date | None,
    hasta: date | None,
) -> WasteReportResponse:
    _validate_range(desde, hasta)
    value, quantity = reports_repository.waste_summary(
        db,
        current_user.branch_id,
        desde,
        hasta,
    )
    items = [
        WasteItem(
            medicine_name=row.medicine_name,
            quantity=row.quantity,
            total_value=row.total_value,
        )
        for row in reports_repository.waste_by_medicine(
            db,
            current_user.branch_id,
            desde,
            hasta,
        )
    ]
    return WasteReportResponse(quantity=quantity, total_value=value, items=items)


def inventory_report(db: Session, current_user: User) -> InventoryReportResponse:
    total_units, total_value, medicine_count = reports_repository.inventory_summary(
        db,
        current_user.branch_id,
    )
    return InventoryReportResponse(
        total_units=total_units,
        total_value=total_value,
        medicine_count=medicine_count,
    )


def movements_report(
    db: Session,
    current_user: User,
    desde: date | None,
    hasta: date | None,
) -> list[KardexEntry]:
    _validate_range(desde, hasta)
    return inventory_service.list_kardex(
        db,
        current_user,
        medicine_id=None,
        lot_id=None,
        desde=desde,
        hasta=hasta,
    )


def dashboard(db: Session, current_user: User) -> DashboardResponse:
    report = inventory_report(db, current_user)
    return DashboardResponse(
        **report.model_dump(),
        unread_alerts=reports_repository.unread_alert_count(db, current_user.branch_id),
        expiring_lots=reports_repository.expiring_lot_count(db, current_user.branch_id, 30),
    )


def export_csv(
    db: Session,
    current_user: User,
    report_type: str,
    desde: date | None,
    hasta: date | None,
    days: int,
) -> tuple[str, str]:
    _validate_range(desde, hasta)
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    if report_type == "mermas":
        writer.writerow(["medicine_name", "quantity", "total_value"])
        for item in waste_report(db, current_user, desde, hasta).items:
            writer.writerow([item.medicine_name, item.quantity, item.total_value])
    elif report_type == "proximos-vencer":
        writer.writerow(
            [
                "lot_id",
                "medicine_name",
                "lot_number",
                "expiration_date",
                "days_remaining",
                "quantity",
                "risk_value",
            ]
        )
        for item in expiring_lots(db, current_user, days):
            writer.writerow(
                [
                    item.lot_id,
                    item.medicine_name,
                    item.lot_number,
                    item.expiration_date,
                    item.days_remaining,
                    item.quantity,
                    item.risk_value,
                ]
            )
    elif report_type == "inventario":
        writer.writerow(["medicine_id", "name", "barcode", "minimum_stock", "total_stock"])
        for item in inventory_service.list_inventory(db, current_user, None, None):
            writer.writerow(
                [
                    item.medicine_id,
                    item.name,
                    item.barcode,
                    item.minimum_stock,
                    item.total_stock,
                ]
            )
    elif report_type == "movimientos":
        writer.writerow(
            [
                "created_at",
                "lot_number",
                "user_name",
                "movement_type",
                "quantity",
                "lot_balance",
                "unit_cost",
                "reason",
            ]
        )
        for item in movements_report(db, current_user, desde, hasta):
            writer.writerow(
                [
                    item.created_at.isoformat(),
                    item.lot_number,
                    item.user_name,
                    item.movement_type.value,
                    item.quantity,
                    item.lot_balance,
                    item.unit_cost,
                    item.reason or "",
                ]
            )
    else:
        raise BusinessRuleError("Unknown report type")

    return f"{report_type}.csv", buffer.getvalue()
