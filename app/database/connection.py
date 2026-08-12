import logging
from typing import AsyncGenerator
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)


_url = settings.DATABASE_URL
if _url.startswith("postgresql://"):
    _url = _url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql+asyncpg://", 1)

# Safe diagnostic log — password is never included
_parsed = urlparse(_url)
logger.info(
    "Database engine initialising: driver=%s user=%s host=%s port=%s db=%s",
    _parsed.scheme,
    _parsed.username,
    _parsed.hostname,
    _parsed.port,
    _parsed.path.lstrip("/"),
)

# ---------------------------------------------------------------------------
# Engine
# Supabase Session Pooler requires SSL; asyncpg accepts ssl="require".
# pool_size / max_overflow are appropriate for a session-mode pooler.
# ---------------------------------------------------------------------------
engine = create_async_engine(
    _url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"ssl": "require"},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a scoped async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
