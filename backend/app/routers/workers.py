"""Router for worker management endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.models.worker import Worker
from app.models.action_log import ActionLog
from app.schemas.worker import WorkerCreate, WorkerResponse

router = APIRouter()


@router.post("", response_model=WorkerResponse, status_code=201)
async def create_worker(payload: WorkerCreate, db: AsyncSession = Depends(get_db)):
    """Add a worker to a site. Sets consented_at to now() by default for demo convenience."""
    worker = Worker(
        site_id=payload.site_id,
        name=payload.name,
        phone_number=payload.phone_number,
        preferred_language=payload.preferred_language or "en",
        status="safe",
        consented_at=datetime.now(timezone.utc),
    )
    db.add(worker)
    await db.commit()
    await db.refresh(worker)
    return worker


@router.get("", response_model=list[WorkerResponse])
async def list_workers(
    site_id: uuid.UUID = Query(None, description="Filter workers by site ID (optional)"),
    db: AsyncSession = Depends(get_db),
):
    """List all workers, optionally filtered by site ID."""
    if site_id:
        result = await db.execute(
            select(Worker)
            .where(Worker.site_id == site_id)
            .order_by(Worker.created_at.desc())
        )
    else:
        result = await db.execute(
            select(Worker).order_by(Worker.created_at.desc())
        )
    return result.scalars().all()


@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(worker_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single worker by ID."""
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker


@router.delete("/{worker_id}", status_code=204)
async def delete_worker(worker_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Remove a worker and their action logs from the database."""
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    await db.execute(delete(ActionLog).where(ActionLog.worker_id == worker_id))
    await db.execute(delete(Worker).where(Worker.id == worker_id))
    await db.commit()
    return None
