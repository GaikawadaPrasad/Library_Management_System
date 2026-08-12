from datetime import datetime, timedelta , timezone
from typing import Optional , Any , Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(subject: str, role: str, expires: Optional[timedelta] = None) -> str:
    if expires:
        expire = datetime.now(timezone.utc) + expires
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: Dict[str, Any] = {"sub": subject, "role": role, "type": "access", "exp": expire}
    # encoded_jwt: str = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(subject: str , expires: Optional[timedelta] = None) -> str:
    if expires:
        expires = datetime.now(timezone.utc) + expires
    else:
        expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode: Dict[str , Any] = {
        "sub": subject,
        "type": "refresh",
        "exp": expires
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str, is_refresh: bool = False) -> Dict[str, Any]:
    """Decode and validate a JWT access or refresh token."""
    secret = settings.JWT_REFRESH_SECRET_KEY if is_refresh else settings.JWT_SECRET_KEY
    payload = jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
    expected_type = "refresh" if is_refresh else "access"

    if payload.get("type") != expected_type:
        raise JWTError("Invalid token type")

    return payload