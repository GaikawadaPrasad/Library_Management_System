import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.borrowing import Borrowing, BorrowingStatus
from app.models.book import Book
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.borrowing import BorrowingCreate
from app.services.notification_service import NotificationService


class BorrowingService:

    @staticmethod
    def _calculate_fine(borrowing: Borrowing) -> Decimal:
        """Calculate the fine owed for an active or returned borrowing."""
        reference_dt = borrowing.returned_at or datetime.now(timezone.utc)

        due = borrowing.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if reference_dt.tzinfo is None:
            reference_dt = reference_dt.replace(tzinfo=timezone.utc)

        if reference_dt <= due:
            return Decimal("0.00")

        overdue_days = (reference_dt - due).days
        chargeable_days = max(0, overdue_days - settings.GRACE_PERIOD_DAYS)
        return Decimal(str(round(chargeable_days * settings.DAILY_FINE_AMOUNT, 2)))

    @staticmethod
    async def list_borrowings(
        db: AsyncSession,
        member_id: Optional[uuid.UUID] = None,
        borrow_status: Optional[BorrowingStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Borrowing], int]:
        query = select(Borrowing)
        count_query = select(func.count()).select_from(Borrowing)

        if member_id:
            query = query.where(Borrowing.member_id == member_id)
            count_query = count_query.where(Borrowing.member_id == member_id)
        if borrow_status:
            query = query.where(Borrowing.status == borrow_status)
            count_query = count_query.where(Borrowing.status == borrow_status)

        total = (await db.execute(count_query)).scalar() or 0
        borrowings = list(
            (await db.execute(
                query.order_by(Borrowing.issued_at.desc()).offset(skip).limit(limit)
            )).scalars().all()
        )
        return borrowings, total

    @staticmethod
    async def get_borrowing(db: AsyncSession, borrowing_id: uuid.UUID) -> Borrowing:
        result = await db.execute(select(Borrowing).where(Borrowing.id == borrowing_id))
        borrowing = result.scalar_one_or_none()
        if not borrowing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Borrowing record not found.",
            )
        return borrowing

    @staticmethod
    async def issue_book(
        db: AsyncSession,
        request: BorrowingCreate,
        issued_by_user: User,
    ) -> Borrowing:
        """Issue a book to a member. Enforces borrow limits and availability."""

        # Verify book exists and has available copies
        book = (await db.execute(
            select(Book).where(Book.id == request.book_id)
        )).scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")
        if book.available_copies < 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No available copies of this book.",
            )

        # Verify member exists and is active
        member = (await db.execute(
            select(User).where(User.id == request.member_id)
        )).scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
        if not member.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Member account is deactivated.",
            )

        # Check member borrow limit
        active_count = (await db.execute(
            select(func.count()).select_from(Borrowing).where(
                Borrowing.member_id == request.member_id,
                Borrowing.status.in_([BorrowingStatus.ACTIVE, BorrowingStatus.OVERDUE]),
            )
        )).scalar() or 0

        if active_count >= settings.MAX_BORROW_LIMIT_PER_MEMBER:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Member has reached the maximum borrow limit of "
                    f"{settings.MAX_BORROW_LIMIT_PER_MEMBER} books."
                ),
            )

        # Determine timestamps
        now = datetime.now(timezone.utc)
        due_date = request.due_date or (now + timedelta(days=settings.DEFAULT_BORROW_DAYS))

        # Create borrowing record
        borrowing = Borrowing(
            book_id=request.book_id,
            member_id=request.member_id,
            issued_by=issued_by_user.id,
            issued_at=now,
            due_date=due_date,
            status=BorrowingStatus.ACTIVE,
            fine_amount=Decimal("0.00"),
        )
        db.add(borrowing)

        # Decrement book availability
        book.available_copies -= 1

        # Send notification to member
        await NotificationService.send_notification(
            db=db,
            user_id=request.member_id,
            title="Book Issued",
            message=(
                f'"{book.title}" has been issued to you. '
                f'Due date: {due_date.strftime("%d %b %Y")}.'
            ),
            notification_type=NotificationType.BORROW_ISSUED,
        )

        await db.commit()
        await db.refresh(borrowing)
        return borrowing

    @staticmethod
    async def return_book(
        db: AsyncSession,
        borrowing_id: uuid.UUID,
        current_user: User,
    ) -> Borrowing:
        """Process a book return, calculate fine, update availability."""
        borrowing = await BorrowingService.get_borrowing(db, borrowing_id)

        if borrowing.status == BorrowingStatus.RETURNED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This book has already been returned.",
            )

        now = datetime.now(timezone.utc)
        borrowing.returned_at = now
        fine = BorrowingService._calculate_fine(borrowing)
        borrowing.fine_amount = fine
        borrowing.status = BorrowingStatus.RETURNED

        # Restore book availability
        book = (await db.execute(
            select(Book).where(Book.id == borrowing.book_id)
        )).scalar_one()
        book.available_copies += 1

        # Notify member
        msg = f'"{book.title}" returned successfully.'
        notif_type = NotificationType.RETURN_SUCCESS
        if fine > 0:
            msg += f" Fine assessed: ${fine:.2f}."
            notif_type = NotificationType.FINE_ASSESSED

        await NotificationService.send_notification(
            db=db,
            user_id=borrowing.member_id,
            title="Book Returned",
            message=msg,
            notification_type=notif_type,
        )

        await db.commit()
        await db.refresh(borrowing)
        return borrowing

    @staticmethod
    async def mark_overdue(db: AsyncSession) -> int:
        """Mark all past-due ACTIVE borrowings as OVERDUE and recalculate fines."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Borrowing).where(
                Borrowing.status == BorrowingStatus.ACTIVE,
                Borrowing.due_date < now,
            )
        )
        overdue_list = result.scalars().all()
        count = 0
        for b in overdue_list:
            b.status = BorrowingStatus.OVERDUE
            b.fine_amount = BorrowingService._calculate_fine(b)
            count += 1
        if count:
            await db.commit()
        return count
