import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate


class BookService:

    @staticmethod
    async def list_books(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        available_only: bool = False,
    ) -> Tuple[List[Book], int]:
        query = select(Book)
        count_query = select(func.count()).select_from(Book)

        if search:
            pattern = f"%{search}%"
            search_filter = or_(
                Book.title.ilike(pattern),
                Book.author.ilike(pattern),
                Book.isbn.ilike(pattern),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if category_id:
            query = query.where(Book.category_id == category_id)
            count_query = count_query.where(Book.category_id == category_id)

        if available_only:
            query = query.where(Book.available_copies > 0)
            count_query = count_query.where(Book.available_copies > 0)

        total = (await db.execute(count_query)).scalar() or 0
        books = list(
            (await db.execute(
                query.order_by(Book.title).offset(skip).limit(limit)
            )).scalars().all()
        )
        return books, total

    @staticmethod
    async def get_book(db: AsyncSession, book_id: uuid.UUID) -> Book:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found.",
            )
        return book

    @staticmethod
    async def create_book(db: AsyncSession, request: BookCreate) -> Book:
        if request.isbn:
            existing = (await db.execute(
                select(Book).where(Book.isbn == request.isbn)
            )).scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A book with ISBN '{request.isbn}' already exists.",
                )

        book = Book(
            title=request.title,
            author=request.author,
            isbn=request.isbn,
            description=request.description,
            publisher=request.publisher,
            publication_year=request.publication_year,
            category_id=request.category_id,
            total_copies=request.total_copies,
            available_copies=request.total_copies,
            cover_image_url=request.cover_image_url,
        )
        db.add(book)
        await db.commit()
        await db.refresh(book)
        return book

    @staticmethod
    async def update_book(
        db: AsyncSession, book_id: uuid.UUID, request: BookUpdate
    ) -> Book:
        book = await BookService.get_book(db, book_id)
        update_data = request.model_dump(exclude_unset=True)

        if "total_copies" in update_data:
            new_total = update_data["total_copies"]
            borrowed_copies = book.total_copies - book.available_copies
            if new_total < borrowed_copies:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Cannot reduce total copies below number currently "
                        f"borrowed ({borrowed_copies})."
                    ),
                )
            # Adjust available copies to match new total
            update_data["available_copies"] = new_total - borrowed_copies

        for field, value in update_data.items():
            setattr(book, field, value)

        await db.commit()
        await db.refresh(book)
        return book

    @staticmethod
    async def delete_book(db: AsyncSession, book_id: uuid.UUID) -> None:
        book = await BookService.get_book(db, book_id)
        if book.available_copies < book.total_copies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a book with active borrowings.",
            )
        await db.delete(book)
        await db.commit()

    @staticmethod
    async def update_cover_image(
        db: AsyncSession, book_id: uuid.UUID, image_url: str
    ) -> Book:
        book = await BookService.get_book(db, book_id)
        book.cover_image_url = image_url
        await db.commit()
        await db.refresh(book)
        return book
