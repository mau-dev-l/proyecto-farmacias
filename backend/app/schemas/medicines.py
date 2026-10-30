from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.inventory import LotResponse


class MedicineBase(BaseModel):
    barcode: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    active_ingredient: str | None = Field(default=None, max_length=150)
    presentation: str | None = Field(default=None, max_length=100)
    sale_price: Decimal = Field(ge=0, decimal_places=2)
    minimum_stock: int = Field(default=0, ge=0)


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    barcode: str | None = Field(default=None, min_length=1, max_length=30)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    active_ingredient: str | None = Field(default=None, max_length=150)
    presentation: str | None = Field(default=None, max_length=100)
    sale_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    minimum_stock: int | None = Field(default=None, ge=0)
    active: bool | None = None


class MedicineResponse(MedicineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    active: bool


class BarcodeLookupResponse(MedicineResponse):
    total_stock: int
    lots: list[LotResponse]
