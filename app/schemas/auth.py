import re
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole

class UserRegisterRequest(BaseModel):
    full_name: str = Field(... , min_length= 2 , max_length= 100 )
    email: EmailStr = Field(... , max_length= 100 , example="user@example.com")
    password: str = Field(..., min_length=8, max_length=64, example="password")
    phone: Optional[str] = Field(None, example="+1234567890")
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one digit.")
        return value
    
    
class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., example="admin@library.com")
    password: str = Field(..., example="AdminPassword123!")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="JWT Refresh Token")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole
    profile_image_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}