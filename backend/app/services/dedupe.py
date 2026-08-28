"""Deduplication and cooldown service: prevents double-alerting and spamming workers during heat spikes."""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.action_log import ActionLog
from app.models.worker import Worker
from app.models.heat_snapshot import HeatSnapshot

logger = logging.getLogger(__name__)


async def is_worker_in_cooldown(
    db: AsyncSession,
    worker_id: uuid.UUID,
    channel: Optional[str] = None,
    cooldown_minutes: Optional[int] = None,
) -> bool:
    """Check if this worker was alerted within the cooldown window (default: 30 minutes).

    Only successful/in-flight statuses ('queued', 'delivered', 'acknowledged') trigger cooldown;
    'failed' attempts do not block retries.
    """
    cd_minutes = cooldown_minutes if cooldown_minutes is not None else settings.alert_cooldown_minutes
    if cd_minutes <= 0:
        return False

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=cd_minutes)
    conditions = [
        ActionLog.worker_id == worker_id,
        ActionLog.status.in_(["queued", "delivered", "acknowledged"]),
        ActionLog.created_at >= cutoff,
    ]
    if channel:
        conditions.append(ActionLog.channel == channel)

    result = await db.execute(
        select(ActionLog).where(*conditions).order_by(ActionLog.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def already_notified(
    db: AsyncSession,
    worker_id: uuid.UUID,
    snapshot_id: Optional[uuid.UUID],
    channel: str,
    cooldown_minutes: Optional[int] = None,
) -> bool:
    """Returns True if this worker was already alerted on this channel for this snapshot
    OR within the cooldown window (default: 30 minutes).
    """
    # 1. Check exact snapshot duplicate (prevents double-dispatch for same snapshot record)
    if snapshot_id is not None:
        result = await db.execute(
            select(ActionLog).where(
                ActionLog.worker_id == worker_id,
                ActionLog.heat_snapshot_id == snapshot_id,
                ActionLog.channel == channel,
            ).limit(1)
        )
        if result.scalar_one_or_none() is not None:
            logger.info(
                f"Deduplication hit: worker {worker_id} already notified on {channel} for snapshot {snapshot_id}"
            )
            return True

    # 2. Check 30-minute cooldown window
    cd_minutes = cooldown_minutes if cooldown_minutes is not None else settings.alert_cooldown_minutes
    if cd_minutes and cd_minutes > 0:
        in_cooldown = await is_worker_in_cooldown(
            db=db,
            worker_id=worker_id,
            channel=channel,
            cooldown_minutes=cd_minutes,
        )
        if in_cooldown:
            logger.info(
                f"Cooldown active: worker {worker_id} alerted on {channel} within last {cd_minutes}m. Suppressing alert."
            )
            return True

    return False


async def is_site_in_cooldown(
    db: AsyncSession,
    site_id: uuid.UUID,
    channel: Optional[str] = None,
    cooldown_minutes: Optional[int] = None,
) -> bool:
    """Check if any worker at this site was alerted within the cooldown window."""
    cd_minutes = cooldown_minutes if cooldown_minutes is not None else settings.alert_cooldown_minutes
    if cd_minutes <= 0:
        return False

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=cd_minutes)
    conditions = [
        Worker.site_id == site_id,
        ActionLog.worker_id == Worker.id,
        ActionLog.status.in_(["queued", "delivered", "acknowledged"]),
        ActionLog.created_at >= cutoff,
    ]
    if channel:
        conditions.append(ActionLog.channel == channel)

    result = await db.execute(
        select(ActionLog).join(Worker, ActionLog.worker_id == Worker.id).where(*conditions).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def get_last_notification(
    db: AsyncSession,
    worker_id: uuid.UUID,
    channel: Optional[str] = None,
) -> Optional[ActionLog]:
    """Retrieve the most recent ActionLog record for a worker."""
    conditions = [ActionLog.worker_id == worker_id]
    if channel:
        conditions.append(ActionLog.channel == channel)

    result = await db.execute(
        select(ActionLog).where(*conditions).order_by(ActionLog.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def is_new_extreme_spike(
    db: AsyncSession,
    site_id: uuid.UUID,
    current_risk_level: str,
) -> bool:
    """Check if this snapshot represents a newly transitioned Extreme spike.
    Returns True if previous snapshot was non-extreme or no previous snapshot exists.
    """
    if current_risk_level != "extreme":
        return False

    result = await db.execute(
        select(HeatSnapshot)
        .where(HeatSnapshot.site_id == site_id)
        .order_by(HeatSnapshot.captured_at.desc())
        .offset(1)
        .limit(1)
    )
    previous_snapshot = result.scalar_one_or_none()
    if previous_snapshot is None:
        return True  # First recorded snapshot is extreme -> new spike

    return previous_snapshot.risk_level != "extreme"
