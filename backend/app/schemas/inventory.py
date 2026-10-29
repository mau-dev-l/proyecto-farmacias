from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.entities import MovementType


class InventoryItem(BaseModel):
    medicine_id: int
    name: str
    barcode: str
    minimum_stock: int
    total_stock: int


class LotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    medicine_id: int
    branch_id: int
    supplier_id: int | None
    lot_number: str
    expiration_date: date
    current_quantity: int
    unit_cost: Decimal
    status: str


class EntryRequest(BaseModel):
    medicine_id: int
    lot_number: str = Field(min_length=1, max_length=50)
    expiration_date: date
    quantity: int = Field(gt=0)
    unit_cost: Decimal = Field(ge=0, decimal_places=2)
    supplier_id: int | None = None
    reason: str | None = Field(default=None, max_length=255)


class MovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lot_id: int
    user_id: int
    movement_type: MovementType
    quantity: int
    lot_balance: int
    unit_cost: Decimal
    reason: str | None
    created_at: datetime


class SaleRequest(BaseModel):
    medicine_id: int
    quantity: int = Field(gt=0)
    reason: str | None = Field(default=None, max_length=255)


class SuggestedLot(BaseModel):
    lot_id: int
    lot_number: str
    expiration_date: date
    available_quantity: int
    suggested_quantity: int
