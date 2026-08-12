import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth import require_librarian, require_admin
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse], summary="List all categories (public)")
async def list_categories(db: AsyncSession = Depends(get_db)):
    return await CategoryService.list_categories(db)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get a category by ID (public)",
)
async def get_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await CategoryService.get_category(db, category_id)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category (Librarian+)",
)
async def create_category(
    request: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_librarian),
):
    return await CategoryService.create_category(db, request)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category (Librarian+)",
)
async def update_category(
    category_id: uuid.UUID,
    request: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_librarian),
):
    return await CategoryService.update_category(db, category_id, request)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category (Admin only)",
)
async def delete_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await CategoryService.delete_category(db, category_id)
