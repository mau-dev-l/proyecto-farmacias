from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.entities import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    name: str
    email: EmailStr
    role: UserRole
    active: bool
