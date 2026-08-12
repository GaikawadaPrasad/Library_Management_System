from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file's location (Backend/app/core/config.py)
# so it works no matter which directory you run uvicorn/fastapi from.
_env_file_path = Path(__file__).resolve().parents[2] / ".env"
_ENV_FILE = str(_env_file_path) if _env_file_path.is_file() else None


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000

    DATABASE_URL: str = ""

    JWT_SECRET_KEY: str = ""
    JWT_REFRESH_SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    MAX_BORROW_LIMIT_PER_MEMBER: int = 5
    DEFAULT_BORROW_DAYS: int = 14
    GRACE_PERIOD_DAYS: int = 2
    DAILY_FINE_AMOUNT: float = 5.00
    CORS_ORIGINS: str = ""
    
    # print(f"Loading settings from {_ENV_FILE}")
    # print(f"Database URL: {DATABASE_URL}")
    # print(f"JWT Secret Key: {JWT_SECRET_KEY}")
    # print(f"JWT Refresh Secret Key: {JWT_REFRESH_SECRET_KEY}")

    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")


settings = Settings()
# print(f"Database URL: {settings.DATABASE_URL}")
