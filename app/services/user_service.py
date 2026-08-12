import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.schemas.user import UserUpdate, UserAdminUpdate


class UserService:

    @staticmethod
    async def list_users(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        query = select(User)
        count_query = select(func.count()).select_from(User)

        if role is not None:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_query = count_query.where(User.is_active == is_active)

        total = (await db.execute(count_query)).scalar() or 0
        users = list(
            (await db.execute(
                query.order_by(User.created_at.desc()).offset(skip).limit(limit)
            )).scalars().all()
        )
        return users, total

    @staticmethod
    async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    @staticmethod
    async def update_profile(db: AsyncSession, user: User, request: UserUpdate) -> User:
        """Allow a member to update their own profile fields."""
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def admin_update_user(
        db: AsyncSession, user_id: uuid.UUID, request: UserAdminUpdate
    ) -> User:
        """Admin: update role, active status, and profile fields."""
        user = await UserService.get_user(db, user_id)
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def deactivate_user(db: AsyncSession, user_id: uuid.UUID) -> User:
        """Admin: soft-delete a user by setting is_active = False."""
        user = await UserService.get_user(db, user_id)
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already deactivated.",
            )
        user.is_active = False
        await db.commit()
        await db.refresh(user)
        return user
