import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth import require_librarian, require_admin
from app.models.user import User
from app.schemas.book import BookCreate, BookUpdate, BookResponse
from app.services.book_service import BookService

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("", summary="List books — supports search by title/author/ISBN and filter by category")
async def list_books(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    search: Optional[str] = Query(None, description="Search title, author, or ISBN"),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category UUID"),
    available_only: bool = Query(False, description="Only show books with available copies"),
    db: AsyncSession = Depends(get_db),
):
    books, total = await BookService.list_books(db, skip, limit, search, category_id, available_only)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [BookResponse.model_validate(b) for b in books],
    }


@router.get("/{book_id}", response_model=BookResponse, summary="Get book details (public)")
async def get_book(book_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await BookService.get_book(db, book_id)


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new book to the library (Librarian+)",
)
async def create_book(
    request: BookCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_librarian),
):
    return await BookService.create_book(db, request)


@router.patch(
    "/{book_id}",
    response_model=BookResponse,
    summary="Update book details (Librarian+)",
)
async def update_book(
    book_id: uuid.UUID,
    request: BookUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_librarian),
):
    return await BookService.update_book(db, book_id, request)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book (Admin only) — fails if book has active borrowings",
)
async def delete_book(
    book_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await BookService.delete_book(db, book_id)
