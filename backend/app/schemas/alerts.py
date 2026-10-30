from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.entities import AlertType


class AlertResponse(BaseModel):
    id: int
    lot_id: int
    alert_type: AlertType
    threshold_days: int | None
    read: bool
    created_at: datetime
    medicine_name: str
    lot_number: str
    expiration_date: date
    days_remaining: int
    quantity: int


class AlertConfigurationRequest(BaseModel):
    lead_days: int | None = Field(default=None, ge=1, le=365)
    thresholds: list[int] | None = Field(default=None, min_length=1, max_length=10)

    @model_validator(mode="after")
    def normalize_thresholds(self) -> "AlertConfigurationRequest":
        values = (
            self.thresholds
            if self.thresholds is not None
            else ([self.lead_days] if self.lead_days is not None else [])
        )
        if not values:
            raise ValueError("At least one threshold is required")
        if any(value < 1 or value > 365 for value in values):
            raise ValueError("Thresholds must be between 1 and 365 days")
        self.thresholds = sorted(set(values), reverse=True)
        return self


class AlertConfigurationResponse(BaseModel):
    branch_id: int
    lead_days: int
    thresholds: list[int]


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


class WasteItem(BaseModel):
    medicine_name: str
    quantity: int
    total_value: Decimal


class WasteReportResponse(BaseModel):
    quantity: int
    total_value: Decimal
    items: list[WasteItem] = Field(default_factory=list)


class DashboardResponse(InventoryReportResponse):
    unread_alerts: int
    expiring_lots: int
