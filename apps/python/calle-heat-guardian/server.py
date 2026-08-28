"""FastAPI Webhook & REST Server for CALL-E Heat Guardian."""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from skills.heat_safety_dispatcher.dispatcher import (
    HeatSafetyPayload,
    CallDispatchResult,
    trigger_heat_call,
    poll_call_status,
)
from apps.python.calle-heat-guardian.config import settings

app = FastAPI(
    title="CALL-E Heat Guardian API",
    description="Autonomous Emergency Voice Dispatcher for Outdoor Workforce Heat Safety powered by CALL-E.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "CALL-E Heat Guardian Voice Agent",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok", "calle_base_url": settings.calle_base_url}


@app.post("/dispatch", response_model=CallDispatchResult)
async def dispatch_call(payload: HeatSafetyPayload):
    """Trigger an autonomous outbound emergency phone call to field personnel."""
    try:
        result = await trigger_heat_call(
            payload=payload,
            api_key=settings.calle_api_key,
            base_url=settings.calle_base_url,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/call/{call_id}")
async def get_call_status(call_id: str):
    """Fetch call status and structured worker acknowledgment from CALL-E."""
    try:
        data = await poll_call_status(
            call_id=call_id,
            api_key=settings.calle_api_key,
            base_url=settings.calle_base_url,
            max_wait_seconds=5,
        )
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
