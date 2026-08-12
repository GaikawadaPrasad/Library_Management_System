import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_librarian
from app.models.borrowing import BorrowingStatus
from app.models.user import User, UserRole
from app.schemas.borrowing import BorrowingCreate, BorrowingResponse
from app.services.borrowing_service import BorrowingService

router = APIRouter(prefix="/borrowings", tags=["Borrowings"])


@router.get("", summary="List borrowings — Librarians see all, Members see only their own")
async def list_borrowings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    borrow_status: Optional[BorrowingStatus] = Query(None, alias="status"),
    member_id: Optional[uuid.UUID] = Query(None, description="Filter by member (Librarian+)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Members can only see their own borrowings
    if current_user.role == UserRole.MEMBER:
        member_id = current_user.id

    borrowings, total = await BorrowingService.list_borrowings(
        db, member_id=member_id, borrow_status=borrow_status, skip=skip, limit=limit
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [BorrowingResponse.model_validate(b) for b in borrowings],
    }


@router.get("/my", summary="Get current user's borrowing history")
async def my_borrowings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    borrow_status: Optional[BorrowingStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    borrowings, total = await BorrowingService.list_borrowings(
        db, member_id=current_user.id, borrow_status=borrow_status, skip=skip, limit=limit
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [BorrowingResponse.model_validate(b) for b in borrowings],
    }


@router.get(
    "/{borrowing_id}",
    response_model=BorrowingResponse,
    summary="Get a single borrowing record",
)
async def get_borrowing(
    borrowing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    borrowing = await BorrowingService.get_borrowing(db, borrowing_id)
    # Members can only view their own records
    if current_user.role == UserRole.MEMBER and borrowing.member_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )
    return borrowing


@router.post(
    "",
    response_model=BorrowingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a book to a member (Librarian+)",
)
async def issue_book(
    request: BorrowingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    return await BorrowingService.issue_book(db, request, current_user)


@router.patch(
    "/{borrowing_id}/return",
    response_model=BorrowingResponse,
    summary="Process a book return and calculate fine (Librarian+)",
)
async def return_book(
    borrowing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    return await BorrowingService.return_book(db, borrowing_id, current_user)


@router.post(
    "/mark-overdue",
    summary="Batch-mark all past-due active borrowings as OVERDUE (Librarian+)",
)
async def mark_overdue(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_librarian),
):
    count = await BorrowingService.mark_overdue(db)
    return {"message": f"{count} borrowing(s) marked as overdue."}
