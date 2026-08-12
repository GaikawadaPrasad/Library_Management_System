from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new member account",
)
async def register(
    request: UserRegisterRequest, db: AsyncSession = Depends(get_db)
):
    return await AuthService.register_member(db, request)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login — returns access + refresh tokens",
)
async def login(
    request: UserLoginRequest, db: AsyncSession = Depends(get_db)
):
    return await AuthService.authenticate_user(db, request)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token using a valid refresh token",
)
async def refresh_token(request: RefreshTokenRequest):
    return await AuthService.refresh_tokens(request.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout — confirms session end (client clears token)",
)
async def logout(current_user: User = Depends(get_current_user)):
    """Client is responsible for discarding the token. This endpoint confirms a valid session."""
    return {"message": "Successfully logged out."}
