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
    """
    Normalize database URLs for async SQLAlchemy drivers (asyncpg for PostgreSQL, aiosqlite for SQLite).
    Handles Supabase / Neon / Render connection strings and transaction poolers (PgBouncer).
    """
    url = (raw_url or "").strip()
    connect_args: dict = {}

    # Vercel / serverless writable directory handling for SQLite
    if os.environ.get("VERCEL") and (url.startswith("sqlite") or ":memory:" not in url):
        if not url.startswith("sqlite+aiosqlite:////tmp/"):
            url = "sqlite+aiosqlite:////tmp/thermashift.db"

    # SQLite normalizations
    if url.startswith("sqlite://"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        connect_args = {"check_same_thread": False, "timeout": 30}
        return url, connect_args
    elif url.startswith("sqlite+aiosqlite://"):
        connect_args = {"check_same_thread": False, "timeout": 30}
        return url, connect_args

    # PostgreSQL normalizations (postgres:// or postgresql:// -> postgresql+asyncpg://)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

    # Parse and clean query parameters for asyncpg compatibility
    parsed = urllib.parse.urlsplit(url)
    if parsed.query:
        query_params = urllib.parse.parse_qs(parsed.query)
        # asyncpg does not accept sslmode query parameter directly in URL
        if "sslmode" in query_params:
            ssl_val = query_params.pop("sslmode")[0]
            if ssl_val in ("require", "verify-ca", "verify-full", "prefer"):
                connect_args["ssl"] = "require"
        if "ssl" in query_params:
            ssl_val = query_params.pop("ssl")[0]
            if ssl_val.lower() in ("true", "1", "require"):
                connect_args["ssl"] = "require"

        # Reconstruct clean URL without incompatible query params
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))

    # Compatibility with Supabase PgBouncer transaction pooling (ports 6543 / 5432)
    # Disabling statement cache prevents 'prepared statement already exists' errors
    connect_args["statement_cache_size"] = 0
    connect_args["prepared_statement_cache_size"] = 0

    return url, connect_args


db_url, connect_args = normalize_database_url(settings.database_url)

try:
    engine_kwargs: dict = {
        "echo": settings.environment == "development",
    }

    if db_url.startswith("sqlite"):
        engine = create_async_engine(
            db_url,
            connect_args=connect_args,
            **engine_kwargs,
        )
        # Enforce foreign key constraints for SQLite
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 1800
        engine_kwargs["pool_timeout"] = 30

        engine = create_async_engine(
            db_url,
            connect_args=connect_args,
            **engine_kwargs,
        )
except Exception as e:
    logger.warning(f"Failed to create engine for {db_url}: {e}. Falling back to SQLite.")
    db_url = "sqlite+aiosqlite:////tmp/thermashift.db"
    connect_args = {"check_same_thread": False, "timeout": 30}
    engine = create_async_engine(
        db_url,
        connect_args=connect_args,
    )
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma_fallback(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
