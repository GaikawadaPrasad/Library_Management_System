import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User, UserRole
from app.schemas.auth import UserResponse
from app.schemas.user import UserUpdate, UserAdminUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me/profile",
    response_model=UserResponse,
    summary="Get my full profile",
)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch(
    "/me/profile",
    response_model=UserResponse,
    summary="Update my own profile (name, phone, avatar URL)",
)
async def update_my_profile(
    request: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await UserService.update_profile(db, current_user, request)


@router.get(
    "",
    summary="List all users with optional role and active status filter (Admin only)",
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    users, total = await UserService.list_users(db, skip, limit, role, is_active)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [UserResponse.model_validate(u) for u in users],
    }


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user by ID (Admin only)",
)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await UserService.get_user(db, user_id)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Admin: update user role, active status, or profile (Admin only)",
)
async def admin_update_user(
    user_id: uuid.UUID,
    request: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await UserService.admin_update_user(db, user_id, request)


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate a user (soft-delete) — Admin only",
)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await UserService.deactivate_user(db, user_id)
