"""Comprehensive unit & integration tests for Scheduler, Autonomous Poller, and Deduplication."""

import asyncio
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.core.config import settings
from app.models.site import Site
from app.models.worker import Worker
from app.models.heat_snapshot import HeatSnapshot
from app.models.action_log import ActionLog
from app.services import dedupe, risk_engine, notifier
from app.core import scheduler

# In-memory SQLite fixture for dedicated scheduler & deduplication isolation
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_session():
    """Create a temporary in-memory async SQLite database session for unit tests."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_dedupe_exact_snapshot(test_session: AsyncSession):
    """Test deduplication: double alerting for the exact same snapshot is prevented."""
    site = Site(
        id=uuid.uuid4(),
        name="Test Site Alpha",
        polygon_geojson={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        extreme_threshold_f=110.0,
        elevated_threshold_f=100.0,
    )
    test_session.add(site)
    worker = Worker(
        id=uuid.uuid4(),
        site_id=site.id,
        name="John Doe",
        phone_number="+15005550001",
        consented_at=datetime.now(timezone.utc),
        status="safe",
    )
    test_session.add(worker)
    snapshot = HeatSnapshot(
        id=uuid.uuid4(),
        site_id=site.id,
        temperature_f=112.0,
        risk_level="extreme",
    )
    test_session.add(snapshot)
    await test_session.commit()

    # Initially not notified
    assert await dedupe.already_notified(test_session, worker.id, snapshot.id, "voice") is False
    assert await dedupe.already_notified(test_session, worker.id, snapshot.id, "sms") is False

    # Log voice alert
    log = ActionLog(
        worker_id=worker.id,
        heat_snapshot_id=snapshot.id,
        channel="voice",
        status="queued",
        provider_ref="call_123",
    )
    test_session.add(log)
    await test_session.commit()

    # Voice should now report already notified
    assert await dedupe.already_notified(test_session, worker.id, snapshot.id, "voice") is True
    # SMS has not been sent yet for this snapshot (cooldown window has no sms records)
    assert await dedupe.already_notified(test_session, worker.id, snapshot.id, "sms") is False


@pytest.mark.asyncio
async def test_dedupe_30_minute_cooldown_window(test_session: AsyncSession):
    """Test that a worker alerted within 30 minutes is not alerted again for a new snapshot."""
    site_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    snap1_id = uuid.uuid4()
    snap2_id = uuid.uuid4()

    # Log an alert sent 10 minutes ago
    ten_min_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
    log = ActionLog(
        worker_id=worker_id,
        heat_snapshot_id=snap1_id,
        channel="voice",
        status="delivered",
        provider_ref="call_past",
        created_at=ten_min_ago,
    )
    test_session.add(log)
    await test_session.commit()

    # For snap2 (a new snapshot), voice should be in cooldown (within 30 mins)
    in_cooldown = await dedupe.already_notified(
        test_session, worker_id, snap2_id, "voice", cooldown_minutes=30
    )
    assert in_cooldown is True

    # Cooldown check helper
    assert await dedupe.is_worker_in_cooldown(test_session, worker_id, "voice", cooldown_minutes=30) is True
    # Worker is NOT in cooldown for 5-minute cooldown check (since 10m > 5m)
    assert await dedupe.is_worker_in_cooldown(test_session, worker_id, "voice", cooldown_minutes=5) is False


@pytest.mark.asyncio
async def test_dedupe_cooldown_expired(test_session: AsyncSession):
    """Test that an alert sent 35 minutes ago allows a new alert (cooldown expired)."""
    worker_id = uuid.uuid4()
    snap1_id = uuid.uuid4()
    snap2_id = uuid.uuid4()

    # Log an alert sent 35 minutes ago
    thirty_five_min_ago = datetime.now(timezone.utc) - timedelta(minutes=35)
    log = ActionLog(
        worker_id=worker_id,
        heat_snapshot_id=snap1_id,
        channel="voice",
        status="delivered",
        provider_ref="call_old",
        created_at=thirty_five_min_ago,
    )
    test_session.add(log)
    await test_session.commit()

    # With 30-min cooldown, snap2 is NOT in cooldown
    in_cooldown = await dedupe.already_notified(
        test_session, worker_id, snap2_id, "voice", cooldown_minutes=30
    )
    assert in_cooldown is False
    assert await dedupe.is_worker_in_cooldown(test_session, worker_id, "voice", cooldown_minutes=30) is False


@pytest.mark.asyncio
async def test_dedupe_failed_status_allows_retry(test_session: AsyncSession):
    """Test that failed alert attempts do NOT trigger the cooldown window."""
    worker_id = uuid.uuid4()
    snap1_id = uuid.uuid4()
    snap2_id = uuid.uuid4()

    # Failed alert 5 minutes ago
    five_min_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    log = ActionLog(
        worker_id=worker_id,
        heat_snapshot_id=snap1_id,
        channel="voice",
        status="failed",
        transcript="Network connection timeout",
        created_at=five_min_ago,
    )
    test_session.add(log)
    await test_session.commit()

    # Worker cooldown should be False for snap2 because the previous attempt failed
    in_cooldown = await dedupe.is_worker_in_cooldown(test_session, worker_id, "voice", cooldown_minutes=30)
    assert in_cooldown is False

    # already_notified for a NEW snapshot should be False
    assert await dedupe.already_notified(test_session, worker_id, snap2_id, "voice", cooldown_minutes=30) is False


@pytest.mark.asyncio
async def test_is_site_in_cooldown(test_session: AsyncSession):
    """Test site-level cooldown checking across workers."""
    site = Site(
        id=uuid.uuid4(),
        name="Site Beta",
        polygon_geojson={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        extreme_threshold_f=110.0,
        elevated_threshold_f=100.0,
    )
    test_session.add(site)
    worker = Worker(
        id=uuid.uuid4(),
        site_id=site.id,
        name="Jane Smith",
        phone_number="+15005550002",
        consented_at=datetime.now(timezone.utc),
        status="safe",
    )
    test_session.add(worker)
    await test_session.commit()

    # Initially site is not in cooldown
    assert await dedupe.is_site_in_cooldown(test_session, site.id, cooldown_minutes=30) is False

    # Add active action log 15 minutes ago
    fifteen_min_ago = datetime.now(timezone.utc) - timedelta(minutes=15)
    log = ActionLog(
        worker_id=worker.id,
        heat_snapshot_id=uuid.uuid4(),
        channel="sms",
        status="delivered",
        provider_ref="SM_test",
        created_at=fifteen_min_ago,
    )
    test_session.add(log)
    await test_session.commit()

    # Site should now be in cooldown
    assert await dedupe.is_site_in_cooldown(test_session, site.id, cooldown_minutes=30) is True
    assert await dedupe.is_site_in_cooldown(test_session, site.id, channel="sms", cooldown_minutes=30) is True
    assert await dedupe.is_site_in_cooldown(test_session, site.id, channel="voice", cooldown_minutes=30) is False


@pytest.mark.asyncio
async def test_is_new_extreme_spike(test_session: AsyncSession):
    """Test spike transition detection: new extreme vs ongoing extreme."""
    site_id = uuid.uuid4()

    # 1. No previous snapshot -> First extreme is a NEW spike
    assert await dedupe.is_new_extreme_spike(test_session, site_id, "extreme") is True
    assert await dedupe.is_new_extreme_spike(test_session, site_id, "normal") is False

    # 2. Previous snapshot was normal, new is extreme -> NEW spike
    old_snap = HeatSnapshot(
        site_id=site_id,
        temperature_f=95.0,
        risk_level="normal",
        captured_at=datetime.now(timezone.utc) - timedelta(minutes=20),
    )
    test_session.add(old_snap)
    new_extreme_snap = HeatSnapshot(
        site_id=site_id,
        temperature_f=112.0,
        risk_level="extreme",
        captured_at=datetime.now(timezone.utc),
    )
    test_session.add(new_extreme_snap)
    await test_session.commit()

    assert await dedupe.is_new_extreme_spike(test_session, site_id, "extreme") is True

    # 3. Previous snapshot was already extreme -> ONGOING heat (not a new spike transition)
    another_extreme_snap = HeatSnapshot(
        site_id=site_id,
        temperature_f=114.0,
        risk_level="extreme",
        captured_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    test_session.add(another_extreme_snap)
    await test_session.commit()

    assert await dedupe.is_new_extreme_spike(test_session, site_id, "extreme") is False


@pytest.mark.asyncio
async def test_scheduler_check_site_10_minute_caching():
    """Test that _check_site respects 10-minute caching and skips FortyGuard API call."""
    site_id = uuid.uuid4()
    site = Site(
        id=site_id,
        name="Cached Solar Field",
        polygon_geojson={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        extreme_threshold_f=110.0,
        elevated_threshold_f=100.0,
        poll_interval_minutes=10,
    )

    recent_snapshot = HeatSnapshot(
        id=uuid.uuid4(),
        site_id=site_id,
        temperature_f=103.5,
        risk_level="elevated",
        captured_at=datetime.now(timezone.utc) - timedelta(minutes=4),  # 4m old (<10m)
    )

    mock_db = AsyncMock()
    mock_snap_result = MagicMock()
    mock_snap_result.scalar_one_or_none.return_value = recent_snapshot

    mock_site_result = MagicMock()
    mock_site_result.scalar_one_or_none.return_value = site

    mock_db.execute.side_effect = [mock_site_result, mock_snap_result]

    with patch("app.core.scheduler.AsyncSessionLocal") as mock_session_maker, \
         patch("app.core.scheduler.fortyguard.get_site_temperature", new_callable=AsyncMock) as mock_fg:

        mock_session_maker.return_value.__aenter__.return_value = mock_db

        result = await scheduler._check_site(site)

        # Verified: returned cached snapshot without calling FortyGuard API
        assert result == recent_snapshot
        mock_fg.assert_not_called()


@pytest.mark.asyncio
async def test_scheduler_check_site_fetches_when_cache_expired():
    """Test that _check_site fetches from FortyGuard when cache is older than 10 minutes."""
    site_id = uuid.uuid4()
    site = Site(
        id=site_id,
        name="Expired Cache Site",
        polygon_geojson={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        extreme_threshold_f=110.0,
        elevated_threshold_f=100.0,
        poll_interval_minutes=10,
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_site_result = MagicMock()
    mock_site_result.scalar_one_or_none.return_value = site

    # Cache check returns None (expired or no snapshot)
    mock_snap_result = MagicMock()
    mock_snap_result.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [mock_site_result, mock_snap_result]

    raw_fg_response = {
        "data": {
            "activity_id": "act_test_999",
            "result": {
                "stats_data": {
                    "temperature_stats": {"maximum": 44.5}  # 44.5°C = 112.1°F -> EXTREME
                }
            }
        }
    }

    with patch("app.core.scheduler.AsyncSessionLocal") as mock_session_maker, \
         patch("app.core.scheduler.fortyguard.get_site_temperature", new_callable=AsyncMock) as mock_fg, \
         patch("app.core.scheduler.notifier.dispatch", new_callable=AsyncMock) as mock_dispatch, \
         patch("app.core.scheduler.is_new_extreme_spike", new_callable=AsyncMock) as mock_spike:

        mock_session_maker.return_value.__aenter__.return_value = mock_db
        mock_fg.return_value = raw_fg_response
        mock_spike.return_value = True

        result = await scheduler._check_site(site)

        # FortyGuard API called
        mock_fg.assert_called_once_with(site.polygon_geojson)
        # Snapshot saved
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        # Extreme temperature (112.1°F >= 110.0°F) triggers alert dispatch
        mock_dispatch.assert_called_once()
        assert result is not None
        assert result.risk_level == "extreme"


@pytest.mark.asyncio
async def test_poll_loop_iteration_and_cancellation():
    """Test that poll_loop iterates over all sites and shuts down cleanly on CancelledError."""
    site1 = Site(id=uuid.uuid4(), name="Site 1", polygon_geojson={}, extreme_threshold_f=110, elevated_threshold_f=100)
    site2 = Site(id=uuid.uuid4(), name="Site 2", polygon_geojson={}, extreme_threshold_f=110, elevated_threshold_f=100)

    mock_db = AsyncMock()
    mock_sites_res = MagicMock()
    mock_sites_res.scalars.return_value.all.return_value = [site1, site2]
    mock_db.execute.return_value = mock_sites_res

    with patch("app.core.scheduler.AsyncSessionLocal") as mock_session_maker, \
         patch("app.core.scheduler._check_site", new_callable=AsyncMock) as mock_check, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        mock_session_maker.return_value.__aenter__.return_value = mock_db

        # Make sleep raise CancelledError on the poll interval sleep to simulate clean shutdown
        mock_sleep.side_effect = [None, None, asyncio.CancelledError()]

        task = asyncio.create_task(scheduler.poll_loop())
        await task
        assert task.done()

        # Verified: checked both sites
        assert mock_check.call_count == 2
        mock_check.assert_any_call(site1.id)
        mock_check.assert_any_call(site2.id)
