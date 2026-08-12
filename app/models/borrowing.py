import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Numeric, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.user import User


class BorrowingStatus(str, enum.Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"


class Borrowing(TimestampMixin, Base):
    __tablename__ = "borrowings"
    __table_args__ = (
        CheckConstraint("due_date >= issued_at", name="chk_due_after_issued"),
        CheckConstraint("fine_amount >= 0.00", name="chk_fine_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    issued_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[BorrowingStatus] = mapped_column(
        SQLEnum(BorrowingStatus, name="borrowing_status", create_type=False),
        default=BorrowingStatus.ACTIVE,
        index=True,
        nullable=False,
    )
    fine_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    # Relationships
    book: Mapped["Book"] = relationship("Book", back_populates="borrowings", lazy="joined")
    member: Mapped["User"] = relationship(
        "User", foreign_keys=[member_id], back_populates="member_borrowings", lazy="joined"
    )
    issuer: Mapped["User"] = relationship(
        "User", foreign_keys=[issued_by], back_populates="issued_borrowings", lazy="selectin"
    )
