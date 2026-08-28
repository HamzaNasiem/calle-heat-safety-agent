"""Router for work site management endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.models.site import Site
from app.models.worker import Worker
from app.models.heat_snapshot import HeatSnapshot
from app.models.action_log import ActionLog
from app.schemas.site import SiteCreate, SiteResponse

router = APIRouter()


@router.post("", response_model=SiteResponse, status_code=201)
async def create_site(payload: SiteCreate, db: AsyncSession = Depends(get_db)):
    """Register a new work site with its GeoJSON polygon and alert thresholds."""
    site = Site(
        name=payload.name,
        polygon_geojson=payload.polygon_geojson,
        extreme_threshold_f=payload.extreme_threshold_f,
        elevated_threshold_f=payload.elevated_threshold_f,
        poll_interval_minutes=payload.poll_interval_minutes,
        manager_id=payload.manager_id,
    )
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(site_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a work site by ID."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.get("", response_model=list[SiteResponse])
async def list_sites(db: AsyncSession = Depends(get_db)):
    """List all registered work sites."""
    result = await db.execute(select(Site).order_by(Site.created_at.desc()))
    return result.scalars().all()


@router.delete("/{site_id}", status_code=204)
async def delete_site(site_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a work site and its associated workers, snapshots, and action logs."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Delete related snapshots and workers
    workers_res = await db.execute(select(Worker.id).where(Worker.site_id == site_id))
    worker_ids = workers_res.scalars().all()
    if worker_ids:
        await db.execute(delete(ActionLog).where(ActionLog.worker_id.in_(worker_ids)))
        await db.execute(delete(Worker).where(Worker.site_id == site_id))

    await db.execute(delete(HeatSnapshot).where(HeatSnapshot.site_id == site_id))
    await db.execute(delete(Site).where(Site.id == site_id))
    await db.commit()
    return None
