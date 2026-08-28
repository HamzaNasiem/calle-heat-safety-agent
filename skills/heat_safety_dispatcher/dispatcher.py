"""Standalone CALL-E Voice AI Dispatcher for Outdoor Workforce Heat Safety.

Handles outbound conversational call task creation, prompt formatting,
and real-time lifecycle tracking via api.heycall-e.com.
"""

from __future__ import annotations
import asyncio
import logging
import os
import re
from typing import Any
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_CALLE_BASE_URL = "https://api.heycall-e.com/v1"
DEFAULT_CALLE_API_KEY = "iams_live_0UvYeesXBhr5GamQNqqc_b8da836ba3458377b7e17ca3dff69d76527d686f5c889839ea65c6096a0c90ec"


class HeatSafetyPayload(BaseModel):
    phone_number: str = Field(..., description="E.164 phone number")
    worker_name: str = Field(..., description="Worker or Foreman name")
    site_name: str = Field(..., description="Job site name")
    temperature_f: float = Field(..., description="Measured temperature in °F")
    work_rest_ratio: str = Field("15 min work / 45 min rest", description="OSHA work/rest cycle")
    hydration_liters_per_hour: float = Field(1.5, description="Hydration quota in L/hr")
    cooling_refuge_direction: str | None = Field(None, description="Compass bearing to coolest sector")


class CallDispatchResult(BaseModel):
    call_id: str
    status: str
    phone_number: str
    worker_acknowledged: bool = False
    summary: str | None = None
    duration_seconds: int = 0
    raw_response: dict[str, Any] = Field(default_factory=dict)


def format_e164(phone: str) -> str:
    """Sanitize and format phone number to strict E.164 standard."""
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    if not cleaned.startswith("+"):
        if len(cleaned) == 10:
            cleaned = "+1" + cleaned
        elif len(cleaned) == 11 and cleaned.startswith("1"):
            cleaned = "+" + cleaned
        else:
            cleaned = "+" + cleaned
    return cleaned


def build_dispatch_prompt(payload: HeatSafetyPayload) -> str:
    """Generate dynamic, safety-compliant conversational instructions for CALL-E."""
    e164_phone = format_e164(payload.phone_number)
    refuge_msg = f" Guide them immediately towards the shaded cooling sector in the {payload.cooling_refuge_direction}." if payload.cooling_refuge_direction else ""
    return (
        f"Call {e164_phone} and immediately speak in fluent, professional, authoritative English to worker {payload.worker_name}. "
        f"You are the CALL-E Heat Guardian autonomous Safety Voice Agent for {payload.site_name}. "
        f"Inform them immediately that the on-site ground microclimate has reached {payload.temperature_f:.1f}°F, crossing hazardous Cal/OSHA thermal strain limits. "
        f"Instruct them to enforce the mandatory {payload.work_rest_ratio} protocol and mandate {payload.hydration_liters_per_hour:.1f} Liters of cool water per hour.{refuge_msg} "
        f"Ask them clearly: 'Do you confirm and acknowledge that you will enforce this safety break immediately?' "
        f"Wait for their verbal response and confirm receipt before ending the call politely."
    )


async def trigger_heat_call(
    payload: HeatSafetyPayload,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float = 30.0,
) -> CallDispatchResult:
    """Place an outbound phone call task to CALL-E API."""
    key = (api_key or os.getenv("CALLE_API_KEY") or DEFAULT_CALLE_API_KEY).strip()
    url = (base_url or os.getenv("CALLE_BASE_URL") or DEFAULT_CALLE_BASE_URL).strip().rstrip("/")
    e164_phone = format_e164(payload.phone_number)

    task_prompt = build_dispatch_prompt(payload)

    task_body = {
        "task": task_prompt,
        "result_schema": {
            "type": "object",
            "required": ["worker_acknowledged"],
            "properties": {
                "worker_acknowledged": {
                    "type": "boolean",
                    "description": "Whether the worker confirmed receipt of the heat evacuation warning and moving to shade"
                }
            },
            "additionalProperties": False
        },
        "metadata": {
            "phone_number": e164_phone,
            "worker_name": payload.worker_name,
            "site_name": payload.site_name,
            "temperature_f": float(payload.temperature_f),
            "system": "CALL-E Heat Guardian"
        }
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        try:
            resp = await client.post(
                f"{url}/calls",
                json=task_body,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            call_id = data.get("call_id") or data.get("id") or (data.get("data", {}).get("call_id") if isinstance(data.get("data"), dict) else f"call_{e164_phone[-6:]}")
            status = data.get("status") or (data.get("data", {}).get("status") if isinstance(data.get("data"), dict) else "queued")

            return CallDispatchResult(
                call_id=str(call_id),
                status=str(status),
                phone_number=e164_phone,
                worker_acknowledged=False,
                summary=f"Dispatched heat advisory to {payload.worker_name} ({e164_phone}) for {payload.site_name} at {payload.temperature_f}°F.",
                raw_response=data,
            )
        except httpx.HTTPStatusError as exc:
            logger.error(f"CALL-E API error {exc.response.status_code}: {exc.response.text}")
            raise RuntimeError(f"CALL-E API returned HTTP {exc.response.status_code}: {exc.response.text}")
        except Exception as exc:
            logger.error(f"CALL-E dispatch failure: {exc}")
            raise RuntimeError(f"Failed to connect to CALL-E: {exc}")


async def poll_call_status(
    call_id: str,
    api_key: str | None = None,
    base_url: str | None = None,
    max_wait_seconds: int = 60,
    poll_interval_seconds: float = 3.0,
) -> dict[str, Any]:
    """Poll CALL-E for completed call details, duration, transcript, and structured acknowledgment."""
    key = (api_key or os.getenv("CALLE_API_KEY") or DEFAULT_CALLE_API_KEY).strip()
    url = (base_url or os.getenv("CALLE_BASE_URL") or DEFAULT_CALLE_BASE_URL).strip().rstrip("/")
    headers = {"Authorization": f"Bearer {key}"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        elapsed = 0.0
        while elapsed < max_wait_seconds:
            try:
                resp = await client.get(f"{url}/calls/{call_id}", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status") or (data.get("data", {}).get("status") if isinstance(data.get("data"), dict) else None)
                    if status in ("completed", "ended", "failed", "busy", "no-answer"):
                        return data
            except Exception:
                pass
            await asyncio.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds

    return {"status": "in-progress", "call_id": call_id}
