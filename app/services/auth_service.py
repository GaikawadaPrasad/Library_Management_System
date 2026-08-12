from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User, UserRole
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse


class AuthService:

    @staticmethod
    async def register_member(
        db: AsyncSession, request: UserRegisterRequest
    ) -> User:
        """Register a new member in the library system."""
        existing = (await db.execute(
            select(User).where(User.email == request.email)
        )).scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        new_user = User(
            full_name=request.full_name,
            email=request.email,
            phone=request.phone,
            password_hash=hash_password(request.password),
            role=UserRole.MEMBER,
            is_active=True,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, request: UserLoginRequest
    ) -> TokenResponse:
        """Authenticate user credentials and issue JWT tokens."""
        user = (await db.execute(
            select(User).where(User.email == request.email)
        )).scalar_one_or_none()

        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )

        access_token = create_access_token(subject=str(user.id), role=user.role.value)
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    @staticmethod
    async def refresh_tokens(refresh_token_str: str) -> TokenResponse:
        """Issue new access and refresh tokens using a valid refresh token."""
        try:
            payload = decode_token(refresh_token_str, is_refresh=True)
            user_id: str = payload.get("sub")
            if not user_id:
                raise JWTError()
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        access_token = create_access_token(
            subject=user_id, role=payload.get("role", "member")
        )
        new_refresh_token = create_refresh_token(subject=user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )
