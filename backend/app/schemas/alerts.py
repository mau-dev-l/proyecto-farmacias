from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.entities import AlertType


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lot_id: int
    alert_type: AlertType
    threshold_days: int | None
    read: bool
    created_at: datetime


class AlertConfigurationRequest(BaseModel):
    lead_days: int = Field(ge=1, le=365)


class AlertConfigurationResponse(BaseModel):
    branch_id: int
    lead_days: int


class ExpiringLotResponse(BaseModel):
    lot_id: int
    medicine_name: str
    lot_number: str
    expiration_date: date
    days_remaining: int
    quantity: int
    risk_value: Decimal


class InventoryReportResponse(BaseModel):
    total_units: int
    total_value: Decimal
    medicine_count: int


class DashboardResponse(InventoryReportResponse):
    unread_alerts: int
    expiring_lots: int
