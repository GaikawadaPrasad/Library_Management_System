"""
db_connectivity_test.py
Run this ONCE to verify the database connection before starting FastAPI.
Never prints the password.
Usage: venv\\Scripts\\python.exe db_connectivity_test.py
"""
import asyncio
import sys
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


def _mask(url: str) -> str:
    """Return URL with password replaced by ****"""
    try:
        p = urlparse(url)
        if p.password:
            return url.replace(f":{p.password}@", ":****@", 1)
    except Exception:
        pass
    return url


async def test_connection(raw_url: str) -> bool:
    # Rewrite scheme for asyncpg
    url = raw_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    print(f"\n=== Database Connectivity Diagnostic ===")
    print(f"  driver   : {parsed.scheme}")
    print(f"  username : {parsed.username}")
    print(f"  hostname : {parsed.hostname}")
    print(f"  port     : {parsed.port}")
    print(f"  database : {parsed.path.lstrip('/')}")
    print(f"  masked   : {_mask(url)}")
    print()

    engine = create_async_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        connect_args={"ssl": "require"},
    )
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            print(f"  SELECT 1 => {value}")
            print("  Connection: OK")
            return True
    except Exception as exc:
        # Never print exc directly as it may contain the password
        msg = str(exc)
        # Mask password if present in error message
        if parsed.password and parsed.password in msg:
            msg = msg.replace(parsed.password, "****")
        print(f"  Connection FAILED: {type(exc).__name__}: {msg}")
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import os
    from pathlib import Path

    env_path = Path(__file__).parent / ".env"
    db_url = ""
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                db_url = line[len("DATABASE_URL="):]
                break

    if not db_url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)

    ok = asyncio.run(test_connection(db_url))
    sys.exit(0 if ok else 1)
