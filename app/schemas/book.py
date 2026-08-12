import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.category import CategoryResponse


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=180)
    isbn: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    publisher: Optional[str] = Field(None, max_length=180)
    publication_year: Optional[int] = None
    category_id: uuid.UUID
    total_copies: int = Field(1, ge=1)
    cover_image_url: Optional[str] = None

    @field_validator("publication_year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1000 or v > 2100):
            raise ValueError("publication_year must be between 1000 and 2100.")
        return v


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=180)
    isbn: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    publisher: Optional[str] = Field(None, max_length=180)
    publication_year: Optional[int] = None
    category_id: Optional[uuid.UUID] = None
    total_copies: Optional[int] = Field(None, ge=1)
    cover_image_url: Optional[str] = None

    @field_validator("publication_year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1000 or v > 2100):
            raise ValueError("publication_year must be between 1000 and 2100.")
        return v


class BookResponse(BaseModel):
    id: uuid.UUID
    title: str
    author: str
    isbn: Optional[str] = None
    description: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    category_id: uuid.UUID
    category: CategoryResponse
    total_copies: int
    available_copies: int
    cover_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
