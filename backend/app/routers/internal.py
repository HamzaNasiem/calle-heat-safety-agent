"""Internal router: manual trigger endpoint for live demos and testing."""

# P0 FEATURE  -  This endpoint must work before anything else in the alert pipeline.
# It allows live demo control: trigger a heat check (real or synthetic) on demand.
# AGENTS.md rule #4: Build this before the alert pipeline.

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.site import Site
from app.models.heat_snapshot import HeatSnapshot
from app.integrations import fortyguard
from app.services import risk_engine, notifier

router = APIRouter()


class TriggerCheckResponse(BaseModel):
    snapshot_id: uuid.UUID
    risk_level: str
    temperature_f: float
    triggered_at: datetime
    alerts_dispatched: bool


@router.post("/trigger-check", response_model=TriggerCheckResponse)
async def trigger_check(
    site_id: uuid.UUID = Query(..., description="Site to run a heat check on"),
    force_extreme: bool = Query(
        False,
        description="If True, inject a synthetic 112°F extreme snapshot (for live demo timing)",
    ),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """Manual heat check trigger. Use force_extreme=true on demo day for guaranteed timing."""
    # Fetch site
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")

    if force_extreme:
        # Synthetic extreme snapshot  -  guarantees demo works regardless of live weather
        temp_f = 112.0
        level = risk_engine.RiskLevel.EXTREME
        activity_id = "synthetic-demo"
        raw = {"synthetic": True, "temperature_f": temp_f}
    else:
        # Real FortyGuard call
        try:
            raw = await fortyguard.get_site_temperature(site.polygon_geojson)
            temp_f = fortyguard.extract_temperature(raw)
            level = risk_engine.classify_risk(
                temperature_f=temp_f,
                elevated_threshold=float(site.elevated_threshold_f),
                extreme_threshold=float(site.extreme_threshold_f),
            )
            activity_id = raw.get("data", {}).get("activity_id") or raw.get("activity_id", "")
        except fortyguard.FortyGuardError as exc:
            raise HTTPException(status_code=502, detail=f"FortyGuard API error: {exc}")

    # Persist snapshot
    snapshot = HeatSnapshot(
        site_id=site.id,
        fortyguard_activity_id=activity_id,
        temperature_f=temp_f,
        analysis_layer="snapshot",
        risk_level=level.value,
        raw_response=raw,
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)

    # Dispatch alerts if extreme
    dispatched = False
    if level == risk_engine.RiskLevel.EXTREME:
        if background_tasks:
            background_tasks.add_task(notifier.dispatch_background, site.id, snapshot.id)
        else:
            await notifier.dispatch(db, site, snapshot)
        dispatched = True

    return TriggerCheckResponse(
        snapshot_id=snapshot.id,
        risk_level=snapshot.risk_level,
        temperature_f=float(snapshot.temperature_f),
        triggered_at=datetime.now(timezone.utc),
        alerts_dispatched=dispatched,
    )


class EnvParamsRequest(BaseModel):
    latitude: float
    longitude: float
    temperature: float
    target_date: str | None = None
    target_time: str | None = None


@router.get("/fortyguard/usage")
async def fortyguard_usage():
    """Fetch current API credit usage and subscription status from FortyGuard /v1/system/fetch-api-key-usage."""
    try:
        return await fortyguard.fetch_api_usage()
    except fortyguard.FortyGuardError as exc:
        raise HTTPException(status_code=502, detail=f"FortyGuard API error: {exc}")


@router.post("/fortyguard/env-params")
async def fortyguard_env_params(payload: EnvParamsRequest):
    """Query environmental parameters via FortyGuard /v1/env_params and poll result."""
    try:
        return await fortyguard.get_env_params(
            latitude=payload.latitude,
            longitude=payload.longitude,
            temperature=payload.temperature,
            target_date=payload.target_date,
            target_time=payload.target_time,
        )
    except fortyguard.FortyGuardError as exc:
        raise HTTPException(status_code=502, detail=f"FortyGuard API error: {exc}")


@router.get("/calle/call/{call_id}")
async def calle_call_status(call_id: str):
    """Fetch live call execution status, task result, and summary from CALL-E."""
    import httpx
    from app.integrations import calle
    
    clean_id = (call_id or "").strip()
    if not clean_id:
        raise HTTPException(status_code=400, detail="call_id cannot be empty")
        
    try:
        status_data = await calle.get_call_status(clean_id)
        try:
            events_data = await calle.get_call_events(clean_id)
        except Exception:
            events_data = {}
        return {"call": status_data, "events": events_data}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"CALL-E call '{clean_id}' not found")
        raise HTTPException(status_code=502, detail=f"CALL-E API error ({exc.response.status_code}): {exc.response.text}")
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"CALL-E API error: {exc}")


class DirectCallRequest(BaseModel):
    phone_number: str
    worker_name: str = "Field Worker"


@router.post("/calle/direct-call")
async def calle_direct_call(payload: DirectCallRequest):
    """Dispatch a real CALL-E outbound call directly to any phone number.
    No DB worker or site record required — used by DirectCallModal for live demos.
    """
    import httpx
    from app.integrations.calle import trigger_direct_call
    try:
        call_id = await trigger_direct_call(
            phone_number=payload.phone_number,
            worker_name=payload.worker_name,
        )
        return {
            "call_id": call_id,
            "status": "queued",
            "phone_number": payload.phone_number,
            "worker_name": payload.worker_name,
            "message": "CALL-E voice call dispatched. Your phone will ring shortly.",
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"CALL-E API error ({exc.response.status_code}): {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"CALL-E dispatch error: {exc}")
