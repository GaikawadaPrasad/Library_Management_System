import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.borrowing import Borrowing


class Book(TimestampMixin, Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("total_copies >= 0", name="chk_total_copies_non_negative"),
        CheckConstraint("available_copies >= 0", name="chk_available_copies_non_negative"),
        CheckConstraint("available_copies <= total_copies", name="chk_available_lte_total"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    author: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    isbn: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    total_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_copies: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cover_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    category: Mapped["Category"] = relationship(
        "Category", back_populates="books", lazy="joined"
    )
    borrowings: Mapped[List["Borrowing"]] = relationship(
        "Borrowing", back_populates="book", lazy="raise"
    )
