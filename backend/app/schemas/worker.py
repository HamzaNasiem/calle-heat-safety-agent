"""Pydantic request/response schemas for workers."""

import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class WorkerCreate(BaseModel):
    site_id: uuid.UUID
    name: str
    phone_number: str
    preferred_language: str = "en"


class WorkerUpdate(BaseModel):
    name: str | None = None
    phone_number: str | None = None
    preferred_language: str | None = None
    status: str | None = None
    consented_at: datetime | None = None


class WorkerResponse(BaseModel):
    id: uuid.UUID
    site_id: uuid.UUID
    name: str
    phone_number: str
    preferred_language: str
    status: str
    consented_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
