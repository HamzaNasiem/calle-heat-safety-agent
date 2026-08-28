"""Orchestrates alert dispatch: voice call via CALL-E + SMS fallback via Twilio."""

import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import AsyncSessionLocal
from app.models.site import Site
from app.models.worker import Worker
from app.models.heat_snapshot import HeatSnapshot
from app.models.action_log import ActionLog
from app.services.dedupe import already_notified
from app.integrations import calle, twilio_sms
from app.integrations.calle import format_e164

logger = logging.getLogger(__name__)


async def _log_action(
    db: AsyncSession,
    worker_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    channel: str,
    status: str,
    provider_ref: str | None = None,
    transcript: str | None = None,
) -> ActionLog | None:
    """Helper to safely create and persist an action log entry with DB deduplication handling (uq_worker_snapshot_channel)."""
    try:
        async with db.begin_nested():
            log = ActionLog(
                worker_id=worker_id,
                heat_snapshot_id=snapshot_id,
                channel=channel,
                provider_ref=provider_ref,
                status=status,
                transcript=transcript,
            )
            db.add(log)
            await db.flush()
            return log
    except IntegrityError as exc:
        logger.warning(
            f"Deduplication constraint (uq_worker_snapshot_channel) prevented duplicate log "
            f"for worker={worker_id}, snapshot={snapshot_id}, channel={channel}: {exc}"
        )
        return None


async def dispatch(db: AsyncSession, site: Site, snapshot: HeatSnapshot) -> None:
    """Dispatch voice + SMS alerts to all consented, non-already-notified active workers."""
    result = await db.execute(
        select(Worker).where(
            Worker.site_id == site.id,
            Worker.consented_at.is_not(None),
        )
    )
    workers = result.scalars().all()

    if not workers:
        logger.info(f"No consented workers found for site {site.name} ({site.id})")
        return

    for worker in workers:
        if worker.consented_at is None:
            continue

        try:
            e164_phone = format_e164(worker.phone_number)
            worker.phone_number = e164_phone
        except Exception as exc:
            logger.error(f"Invalid phone number format for worker {worker.name}: {exc}")
            continue

        notification_attempted = False

        # 1. Voice Call via CALL-E (HeyCall-E)
        if not await already_notified(db, worker.id, snapshot.id, "voice"):
            try:
                call_id = await calle.trigger_outbound_call(worker, site, snapshot)
                await _log_action(
                    db=db,
                    worker_id=worker.id,
                    snapshot_id=snapshot.id,
                    channel="voice",
                    status="queued",
                    provider_ref=call_id,
                )
                notification_attempted = True
                logger.info(f"CALL-E voice call queued for worker {worker.name}: call_id={call_id}")
            except Exception as exc:
                logger.error(f"CALL-E voice call failed for worker {worker.name}: {exc}")
                await _log_action(
                    db=db,
                    worker_id=worker.id,
                    snapshot_id=snapshot.id,
                    channel="voice",
                    status="failed",
                    transcript=str(exc),
                )

        # 2. SMS Fallback via Twilio
        if not await already_notified(db, worker.id, snapshot.id, "sms"):
            try:
                sms_sid = twilio_sms.send_sms(worker, site, snapshot)
                await _log_action(
                    db=db,
                    worker_id=worker.id,
                    snapshot_id=snapshot.id,
                    channel="sms",
                    status="delivered",
                    provider_ref=sms_sid,
                )
                notification_attempted = True
                logger.info(f"SMS sent to worker {worker.name}: sid={sms_sid}")
            except Exception as exc:
                logger.error(f"SMS failed for worker {worker.name}: {exc}")
                await _log_action(
                    db=db,
                    worker_id=worker.id,
                    snapshot_id=snapshot.id,
                    channel="sms",
                    status="failed",
                    transcript=str(exc),
                )

        if notification_attempted:
            worker.status = "notified"

    await db.commit()


async def dispatch_background(site_id: uuid.UUID, snapshot_id: uuid.UUID) -> None:
    """Execute dispatch in background task with dedicated database session."""
    async with AsyncSessionLocal() as session:
        site_res = await session.execute(select(Site).where(Site.id == site_id))
        site = site_res.scalar_one_or_none()
        snap_res = await session.execute(select(HeatSnapshot).where(HeatSnapshot.id == snapshot_id))
        snapshot = snap_res.scalar_one_or_none()

        if site and snapshot:
            await dispatch(session, site, snapshot)
