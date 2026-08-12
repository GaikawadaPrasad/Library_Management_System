import uuid
from typing import List
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:

    @staticmethod
    async def list_categories(db: AsyncSession) -> List[Category]:
        result = await db.execute(select(Category).order_by(Category.name))
        return list(result.scalars().all())

    @staticmethod
    async def get_category(db: AsyncSession, category_id: uuid.UUID) -> Category:
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found.",
            )
        return category

    @staticmethod
    async def create_category(db: AsyncSession, request: CategoryCreate) -> Category:
        existing = (await db.execute(
            select(Category).where(Category.name == request.name)
        )).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{request.name}' already exists.",
            )
        category = Category(name=request.name, description=request.description)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def update_category(
        db: AsyncSession, category_id: uuid.UUID, request: CategoryUpdate
    ) -> Category:
        category = await CategoryService.get_category(db, category_id)
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete_category(db: AsyncSession, category_id: uuid.UUID) -> None:
        category = await CategoryService.get_category(db, category_id)
        await db.delete(category)
        await db.commit()
