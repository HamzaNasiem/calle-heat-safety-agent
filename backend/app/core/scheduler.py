"""Autonomous background poller for ThermaShift AI.
Polls FortyGuard microclimate data for all registered sites with 10-minute caching
and triggers voice calls/SMS alerts on Extreme heat spikes with 30-minute cooldown deduplication.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Union

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.site import Site
from app.models.heat_snapshot import HeatSnapshot
from app.integrations import fortyguard
from app.services import risk_engine, notifier
from app.services.dedupe import is_new_extreme_spike

logger = logging.getLogger(__name__)

# Standard microclimate caching TTL (minutes) to prevent redundant API calls and rate-limiting
DEFAULT_CACHE_TTL_MINUTES = 10


async def _check_site(site_or_id: Union[Site, uuid.UUID]) -> Optional[HeatSnapshot]:
    """Fetch microclimate temperature for a single site with 10-minute caching.
    
    1. Checks DB for snapshot within the last 10 minutes (or site.poll_interval_minutes).
    2. If cached, skips API call to conserve FortyGuard credits and prevent rate limits.
    3. If expired/missing, queries FortyGuard API, classifies risk thresholds, and persists snapshot.
    4. Triggers voice/SMS alerts if Extreme heat is detected, enforcing 30-minute cooldown.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Resolve Site object
            if isinstance(site_or_id, uuid.UUID):
                site_res = await db.execute(select(Site).where(Site.id == site_or_id))
                site = site_res.scalar_one_or_none()
                if not site:
                    logger.warning(f"Site {site_or_id} not found in database.")
                    return None
            else:
                site_res = await db.execute(select(Site).where(Site.id == site_or_id.id))
                site = site_res.scalar_one_or_none() or site_or_id

            # 1. 10-Minute Caching Check
            cache_ttl_minutes = (
                getattr(site, "poll_interval_minutes", None)
                or settings.default_poll_interval_minutes
                or DEFAULT_CACHE_TTL_MINUTES
            )
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=cache_ttl_minutes)

            snap_res = await db.execute(
                select(HeatSnapshot)
                .where(
                    HeatSnapshot.site_id == site.id,
                    HeatSnapshot.captured_at >= cutoff,
                )
                .order_by(HeatSnapshot.captured_at.desc())
                .limit(1)
            )
            existing = snap_res.scalar_one_or_none()
            if existing:
                logger.info(
                    f"Site '{site.name}' ({site.id}) has fresh microclimate snapshot "
                    f"({existing.temperature_f}°F, {existing.risk_level}, {existing.captured_at}). "
                    f"Skipping FortyGuard API call (cached within {cache_ttl_minutes}m)."
                )
                return existing

            # 2. Fetch live microclimate data from FortyGuard
            logger.info(f"Polling FortyGuard microclimate API for site '{site.name}' ({site.id})")
            raw = await fortyguard.get_site_temperature(site.polygon_geojson)
            temp_f = fortyguard.extract_temperature(raw)

            # 3. Evaluate risk thresholds
            level = risk_engine.classify_risk(
                temperature_f=temp_f,
                elevated_threshold=float(site.elevated_threshold_f),
                extreme_threshold=float(site.extreme_threshold_f),
            )

            snapshot = HeatSnapshot(
                site_id=site.id,
                fortyguard_activity_id=(
                    raw.get("data", {}).get("activity_id") or raw.get("activity_id")
                ),
                temperature_f=temp_f,
                analysis_layer="snapshot",
                risk_level=level.value,
                raw_response=raw,
            )
            db.add(snapshot)
            await db.commit()
            await db.refresh(snapshot)
            logger.info(
                f"Recorded heat snapshot for '{site.name}': {temp_f}°F -> {level.value.upper()}"
            )

            # 4. Trigger voice calls & SMS on Extreme heat with 30-minute cooldown deduplication
            if level == risk_engine.RiskLevel.EXTREME:
                new_spike = await is_new_extreme_spike(db, site.id, level.value)
                logger.warning(
                    f"CRITICAL: Extreme heat hazard detected at site '{site.name}' "
                    f"({temp_f}°F >= {site.extreme_threshold_f}°F). "
                    f"Spike status: {'NEW SPIKE' if new_spike else 'ONGOING HEAT'}. "
                    f"Dispatching alerts with 30-min cooldown deduplication..."
                )
                await notifier.dispatch(db, site, snapshot)

            return snapshot
        except Exception as exc:
            logger.error(
                f"Error polling site {getattr(site_or_id, 'id', site_or_id)}: {exc}",
                exc_info=True,
            )
            return None


async def poll_loop() -> None:
    """Autonomous poller loop: iterates through all registered sites in DB.
    
    - Executes every poll interval (default: 10 minutes).
    - Protects FortyGuard credits with 10-minute microclimate caching.
    - Prevents burst traffic with 1-second delay between sites.
    - Dispatches alerts only on Extreme spikes with 30-minute cooldown.
    - Handles async cancellation gracefully on application shutdown.
    """
    logger.info(
        "Autonomous background poller started (10-minute microclimate cache, 30-minute alert cooldown)"
    )
    try:
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(Site))
                    sites = result.scalars().all()
                    site_ids = [s.id for s in sites]

                logger.info(f"Background poller cycle starting for {len(site_ids)} registered site(s)")
                for site_id in site_ids:
                    await _check_site(site_id)
                    # 1.0s delay between sites to prevent API burst traffic and rate limiting
                    await asyncio.sleep(1.0)

            except asyncio.CancelledError:
                logger.info("Background poller cancelled during site iteration.")
                raise
            except Exception as exc:
                logger.error(f"Background poller iteration error: {exc}", exc_info=True)

            poll_interval_sec = (
                getattr(settings, "default_poll_interval_minutes", 10) * 60
            )
            logger.info(f"Background poller cycle complete. Sleeping for {poll_interval_sec}s ({poll_interval_sec // 60}m)...")
            await asyncio.sleep(poll_interval_sec)

    except asyncio.CancelledError:
        logger.info("Background poller task shut down gracefully.")
