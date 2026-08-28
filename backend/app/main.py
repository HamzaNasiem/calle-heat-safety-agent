"""FastAPI application entrypoint for ThermaShift AI."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.scheduler import poll_loop
from app.routers import sites, workers, heat, alerts, internal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.core.database import engine, Base, AsyncSessionLocal
from app.models.site import Site
from app.models.worker import Worker
from app.models.heat_snapshot import HeatSnapshot
from app.models.action_log import ActionLog
from sqlalchemy import select

import os
import httpx

_poller_task: asyncio.Task | None = None
_keepalive_task: asyncio.Task | None = None


async def keep_alive_self_ping():
    """Self-ping loop every 4 minutes to guarantee inbound HTTP traffic and zero spin-down on Render."""
    base_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("BACKEND_URL") or "https://thermashift-ai.onrender.com"
    ping_url = f"{base_url.rstrip('/')}/health"
    logger.info(f"Keep-alive self-ping loop active targeting {ping_url}")
    try:
        while True:
            try:
                await asyncio.sleep(240)  # Ping every 4 minutes
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(ping_url)
                    logger.info(f"Keep-Alive self-ping: status {resp.status_code}")
            except asyncio.CancelledError:
                logger.info("Keep-alive self-ping task cancelled.")
                raise
            except Exception as e:
                logger.debug(f"Self-ping notice: {e}")
    except asyncio.CancelledError:
        logger.info("Keep-alive self-ping stopped gracefully.")


async def auto_seed_if_empty():
    """Auto-seed default global industrial sites if DB is fresh with resilient SQLite fallback."""
    import app.models  # Ensures all tables (Site, Worker, etc.) are registered on Base.metadata
    from app.core import database

    # 1. Attempt schema creation on configured engine
    try:
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.warning(f"Primary database connection error ({e}). Falling back to local resilient SQLite...")
        fallback_url = "sqlite+aiosqlite:////tmp/calle_guardian.db" if os.environ.get("RENDER") or os.environ.get("VERCEL") else "sqlite+aiosqlite:///calle_guardian.db"
        database.engine = create_async_engine(
            fallback_url,
            connect_args={"check_same_thread": False, "timeout": 30}
        )
        database.AsyncSessionLocal = async_sessionmaker(
            bind=database.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # 2. Seed default data if database is fresh
    try:
        async with database.AsyncSessionLocal() as db:
            result = await db.execute(select(Site))
            existing = result.scalars().all()
            if not existing:
                logger.info("Fresh database detected. Auto-seeding initial global sites...")
                try:
                    from seed_global_sites import seed_sites
                except ImportError:
                    from backend.seed_global_sites import seed_sites
                await seed_sites()
    except Exception as e:
        logger.warning(f"Auto-seeding notice: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background poller and DB init on startup, cancel and cleanup on shutdown."""
    global _poller_task, _keepalive_task
    await auto_seed_if_empty()
    if settings.environment != "testing":
        _poller_task = asyncio.create_task(poll_loop())
        _keepalive_task = asyncio.create_task(keep_alive_self_ping())
        logger.info("ThermaShift AI backend started with 24/7 background worker & keep-alive engine")
    yield
    # Gracefully cancel and await all running background tasks
    tasks_to_cancel = [t for t in [_poller_task, _keepalive_task] if t is not None]
    for task in tasks_to_cancel:
        task.cancel()
    if tasks_to_cancel:
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

    # Release database connection pool
    await engine.dispose()
    logger.info("ThermaShift AI backend shut down cleanly")


app = FastAPI(
    title="CALL-E Heat Guardian",
    description="Autonomous phone call safety agent for outdoor workers powered by CALL-E Voice AI.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "https://calle-heat-safety.vercel.app",
        "http://localhost:3005",
        "http://localhost:5173",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard direct routes
app.include_router(sites.router, prefix="/sites", tags=["Sites"])
app.include_router(workers.router, prefix="/workers", tags=["Workers"])
app.include_router(heat.router, prefix="/heat", tags=["Heat"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(internal.router, prefix="/internal", tags=["Internal"])

# Dual-mount under /api for 100% serverless & reverse proxy resilience
app.include_router(sites.router, prefix="/api/sites", tags=["Sites API"])
app.include_router(workers.router, prefix="/api/workers", tags=["Workers API"])
app.include_router(heat.router, prefix="/api/heat", tags=["Heat API"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts API"])
app.include_router(internal.router, prefix="/api/internal", tags=["Internal API"])


@app.get("/", tags=["Root"])
@app.get("/api", tags=["Root"])
async def root_index():
    """Service landing endpoint."""
    return {
        "service": "CALL-E Heat Guardian API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "voice_agent": "CALL-E (HeyCall-E) Real Telephony Engine"
    }


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Simple liveness check endpoint."""
    return {"status": "ok", "service": "CALL-E Heat Guardian"}
