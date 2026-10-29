from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.entities import UserRole


class BranchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=255)


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    active: bool | None = None


class BranchResponse(BranchCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    active: bool


class UserCreate(BaseModel):
    branch_id: int
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole


class UserUpdate(BaseModel):
    branch_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    role: UserRole | None = None
    active: bool | None = None
