import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from app.models.borrowing import BorrowingStatus
from app.schemas.book import BookResponse
from app.schemas.user import UserBriefResponse


class BorrowingCreate(BaseModel):
    book_id: uuid.UUID
    member_id: uuid.UUID
    due_date: Optional[datetime] = None  # Defaults to settings.DEFAULT_BORROW_DAYS if None


class BorrowingResponse(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    member_id: uuid.UUID
    issued_by: uuid.UUID
    book: BookResponse
    member: UserBriefResponse
    issuer: UserBriefResponse
    issued_at: datetime
    due_date: datetime
    returned_at: Optional[datetime] = None
    status: BorrowingStatus
    fine_amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
