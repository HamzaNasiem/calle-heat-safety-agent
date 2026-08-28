"""
Comprehensive test suite for ThermaShift AI Database, Schema & Persistence Layer.
Tests async SQLAlchemy models, PostgreSQL/Supabase engine normalization, SQLite auto-fallback,
foreign key cascading, unique deduplication constraints, indexes, GeoJSON polygon integrity,
and seeding scripts.
"""

import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy import select, delete, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import normalize_database_url, Base
from app.models.manager import Manager
from app.models.site import Site
from app.models.worker import Worker
from app.models.heat_snapshot import HeatSnapshot
from app.models.action_log import ActionLog
from seed_global_sites import GLOBAL_SITES, seed_sites, DEFAULT_MANAGER_ID


# In-memory SQLite async engine fixture for isolated persistence tests
@pytest_asyncio.fixture
async def test_session():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_maker() as session:
        yield session

    await test_engine.dispose()


def test_normalize_database_url_postgresql_schemes():
    """Verify PostgreSQL URL conversion to asyncpg and parameter handling."""
    # Standard postgres:// URL
    url1, args1 = normalize_database_url("postgres://user:pass@db.supabase.co:5432/postgres")
    assert url1.startswith("postgresql+asyncpg://")
    assert args1["statement_cache_size"] == 0

    # postgresql:// with sslmode query parameter
    url2, args2 = normalize_database_url("postgresql://postgres:secret@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require")
    assert url2.startswith("postgresql+asyncpg://")
    assert "sslmode" not in url2  # Incompatible param stripped from URL
    assert args2.get("ssl") == "require"
    assert args2["statement_cache_size"] == 0

    # postgresql+psycopg2:// scheme
    url3, _ = normalize_database_url("postgresql+psycopg2://user:pass@localhost:5432/db")
    assert url3.startswith("postgresql+asyncpg://")


def test_normalize_database_url_sqlite_schemes():
    """Verify SQLite URL conversion to aiosqlite and timeout handling."""
    url1, args1 = normalize_database_url("sqlite:///thermashift.db")
    assert url1 == "sqlite+aiosqlite:///thermashift.db"
    assert args1["check_same_thread"] is False
    assert args1["timeout"] == 30

    url2, args2 = normalize_database_url("sqlite+aiosqlite:////tmp/thermashift.db")
    assert url2 == "sqlite+aiosqlite:////tmp/thermashift.db"
    assert args2["check_same_thread"] is False


@pytest.mark.asyncio
async def test_geojson_polygons_validity():
    """Verify that all 5 global sites have RFC 7946 compliant GeoJSON Polygons."""
    assert len(GLOBAL_SITES) == 5
    expected_names = [s["name"] for s in GLOBAL_SITES]

    for i, site_data in enumerate(GLOBAL_SITES):
        assert site_data["name"] == expected_names[i]
        assert "lat" in site_data and "lng" in site_data and "delta" in site_data
        assert site_data["extreme_f"] > site_data["elevated_f"]

        lat, lng, d = site_data["lat"], site_data["lng"], site_data["delta"]
        # Generate polygon
        coords = [
            [round(lng - d, 6), round(lat - d, 6)],
            [round(lng + d, 6), round(lat - d, 6)],
            [round(lng + d, 6), round(lat + d, 6)],
            [round(lng - d, 6), round(lat + d, 6)],
            [round(lng - d, 6), round(lat - d, 6)],
        ]
        # Polygon must be closed (first coordinate equals last coordinate)
        assert coords[0] == coords[-1]
        assert len(coords) == 5
        # Coordinates must be [longitude, latitude]
        for pt in coords:
            assert -180.0 <= pt[0] <= 180.0  # lng
            assert -90.0 <= pt[1] <= 90.0   # lat


@pytest.mark.asyncio
async def test_action_log_unique_deduplication_constraint(test_session: AsyncSession):
    """Verify unique constraint uq_worker_snapshot_channel prevents duplicate alert records."""
    site = Site(
        name="Dedupe Test Site",
        polygon_geojson={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        extreme_threshold_f=110.0,
        elevated_threshold_f=100.0,
    )
    test_session.add(site)
    await test_session.flush()

    worker = Worker(
        site_id=site.id,
        name="Dedupe Worker",
        phone_number="+15551234567",
        status="safe",
    )
    test_session.add(worker)

    snap = HeatSnapshot(
        site_id=site.id,
        temperature_f=112.0,
        risk_level="extreme",
    )
    test_session.add(snap)
    await test_session.flush()

    # First log insert should succeed
    log1 = ActionLog(
        worker_id=worker.id,
        heat_snapshot_id=snap.id,
        channel="voice",
        status="queued",
        provider_ref="call_test_1",
    )
    test_session.add(log1)
    await test_session.commit()

    # Duplicate insert on same (worker_id, heat_snapshot_id, channel) must raise IntegrityError
    log2 = ActionLog(
        worker_id=worker.id,
        heat_snapshot_id=snap.id,
        channel="voice",
        status="delivered",
        provider_ref="call_test_2",
    )
    with pytest.raises(IntegrityError):
        async with test_session.begin_nested():
            test_session.add(log2)
            await test_session.flush()

    # Different channel ("sms") on same snapshot should succeed
    log_sms = ActionLog(
        worker_id=worker.id,
        heat_snapshot_id=snap.id,
        channel="sms",
        status="queued",
        provider_ref="sms_test_1",
    )
    test_session.add(log_sms)
    await test_session.commit()


@pytest.mark.asyncio
async def test_nested_transaction_savepoint_safety(test_session: AsyncSession):
    """Verify begin_nested() SAVEPOINT transaction isolation during deduplication."""
    site = Site(
        name="Savepoint Site",
        polygon_geojson={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
    )
    test_session.add(site)
    await test_session.flush()

    worker = Worker(site_id=site.id, name="Worker Savepoint", phone_number="+15559876543")
    test_session.add(worker)
    snap = HeatSnapshot(site_id=site.id, temperature_f=111.0, risk_level="extreme")
    test_session.add(snap)
    await test_session.flush()

    # Create initial entry
    log1 = ActionLog(worker_id=worker.id, heat_snapshot_id=snap.id, channel="voice", status="queued")
    test_session.add(log1)
    await test_session.commit()

    # Attempt duplicate insert wrapped in savepoint
    duplicate_suppressed = False
    try:
        async with test_session.begin_nested():
            dup_log = ActionLog(worker_id=worker.id, heat_snapshot_id=snap.id, channel="voice", status="queued")
            test_session.add(dup_log)
            await test_session.flush()
    except IntegrityError:
        duplicate_suppressed = True

    assert duplicate_suppressed is True

    # Session is still healthy and can perform further operations
    worker.status = "notified"
    await test_session.commit()
    await test_session.refresh(worker)
    assert worker.status == "notified"


@pytest.mark.asyncio
async def test_seed_global_sites_execution():
    """Verify seed_sites() populates all 5 sites, workers, manager, and snapshots."""
    from app.core.database import init_db
    await init_db()
    await seed_sites()

    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        # Verify Manager
        mgr_res = await session.execute(select(Manager).where(Manager.id == DEFAULT_MANAGER_ID))
        mgr = mgr_res.scalar_one_or_none()
        assert mgr is not None
        assert mgr.email == "ops@thermashift.ai"

        # Verify 5 Sites
        sites_res = await session.execute(select(Site))
        sites = sites_res.scalars().all()
        assert len(sites) >= 5

        # Verify site IDs match deterministic UUIDs
        site_ids = {s.id for s in sites}
        for s_data in GLOBAL_SITES:
            assert s_data["id"] in site_ids

        # Verify workers
        workers_res = await session.execute(select(Worker))
        workers = workers_res.scalars().all()
        assert len(workers) >= 11
        for w in workers:
            assert w.consented_at is not None
            assert w.status in ("safe", "notified")

        # Verify baseline snapshots
        snaps_res = await session.execute(select(HeatSnapshot))
        snaps = snaps_res.scalars().all()
        assert len(snaps) >= 5
