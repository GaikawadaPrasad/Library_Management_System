import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserBriefResponse(BaseModel):
    """Compact user info embedded in other responses (borrowings, etc.)."""
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Allows a member to update their own profile."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    profile_image_url: Optional[str] = None


class UserAdminUpdate(BaseModel):
    """Allows an admin to update any user's role or active status."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
