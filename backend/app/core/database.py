"""Async SQLAlchemy engine and session factory with automatic fallback and Supabase support."""

import os
import logging
import urllib.parse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from app.core.config import settings

logger = logging.getLogger(__name__)


def normalize_database_url(raw_url: str) -> tuple[str, dict]:
    """Normalize database URLs for async SQLAlchemy drivers with resilient fallback."""
    url = (raw_url or "").strip()
    connect_args: dict = {}

    # Cloud standalone resilient SQLite default
    if not url or url.startswith("sqlite") or ":memory:" in url or (os.environ.get("RENDER") and not os.environ.get("USE_POSTGRES")):
        db_path = "/tmp/calle_guardian.db" if os.environ.get("RENDER") or os.environ.get("VERCEL") else "calle_guardian.db"
        url = f"sqlite+aiosqlite:///{db_path}"
        connect_args = {"check_same_thread": False, "timeout": 30}
        return url, connect_args

    # PostgreSQL normalizations
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

    parsed = urllib.parse.urlsplit(url)
    if parsed.query:
        query_params = urllib.parse.parse_qs(parsed.query)
        if "sslmode" in query_params:
            ssl_val = query_params.pop("sslmode")[0]
            if ssl_val in ("require", "verify-ca", "verify-full", "prefer"):
                connect_args["ssl"] = "require"
        if "ssl" in query_params:
            ssl_val = query_params.pop("ssl")[0]
            if ssl_val.lower() in ("true", "1", "require"):
                connect_args["ssl"] = "require"
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))

    return url, connect_args


db_url, connect_args = normalize_database_url(settings.database_url)

try:
    engine_kwargs: dict = {
        "echo": False,
    }
    if db_url.startswith("sqlite"):
        engine = create_async_engine(db_url, connect_args=connect_args, **engine_kwargs)
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
            except Exception:
                pass
    else:
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 1800
        engine_kwargs["pool_timeout"] = 30
        engine = create_async_engine(db_url, connect_args=connect_args, **engine_kwargs)
except Exception as e:
    logger.warning(f"Engine creation fallback: {e}")
    db_path = "/tmp/calle_guardian.db" if os.environ.get("RENDER") or os.environ.get("VERCEL") else "calle_guardian.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    connect_args = {"check_same_thread": False, "timeout": 30}
    engine = create_async_engine(db_url, connect_args=connect_args)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:  # type: ignore[return]
    """FastAPI dependency that yields an async DB session with automatic rollback on error."""
    from app.core import database
    async with database.AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

async def init_db():
    """Create all tables in the database if they do not exist."""
    from app.core import database
    import app.models  # Ensure all model tables are registered on Base
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
