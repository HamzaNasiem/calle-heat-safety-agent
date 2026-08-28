"""Pydantic response schema for action logs."""

import uuid
from datetime import datetime
from pydantic import BaseModel


class ActionLogResponse(BaseModel):
    id: uuid.UUID
    worker_id: uuid.UUID
    heat_snapshot_id: uuid.UUID | None
    channel: str
    provider_ref: str | None
    status: str
    transcript: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
