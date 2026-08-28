"""Router for alert action log endpoints."""

import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.action_log import ActionLog
from app.models.worker import Worker
from app.schemas.action_log import ActionLogResponse

router = APIRouter()


@router.get("", response_model=list[ActionLogResponse])
async def list_alerts(
    site_id: uuid.UUID | None = Query(None, description="Filter alert logs by site ID (optional)"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Return recent alert action logs for all workers on a site  -  powers the live alert feed."""
    if site_id:
        result = await db.execute(
            select(ActionLog)
            .join(Worker, ActionLog.worker_id == Worker.id)
            .where(Worker.site_id == site_id)
            .order_by(ActionLog.created_at.desc())
            .limit(limit)
        )
    else:
        result = await db.execute(
            select(ActionLog)
            .order_by(ActionLog.created_at.desc())
            .limit(limit)
        )
    return result.scalars().all()
