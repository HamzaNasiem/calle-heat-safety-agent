"""Pydantic request/response schemas for sites."""

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class SiteCreate(BaseModel):
    name: str
    polygon_geojson: dict[str, Any] = Field(..., description="GeoJSON Polygon  -  sent as-is to FortyGuard polygon_aoi")
    extreme_threshold_f: float = 110.0
    elevated_threshold_f: float = 100.0
    poll_interval_minutes: int = 10
    manager_id: uuid.UUID | None = None


class SiteUpdate(BaseModel):
    name: str | None = None
    polygon_geojson: dict[str, Any] | None = None
    extreme_threshold_f: float | None = None
    elevated_threshold_f: float | None = None
    poll_interval_minutes: int | None = None
    manager_id: uuid.UUID | None = None


class SiteResponse(BaseModel):
    id: uuid.UUID
    name: str
    polygon_geojson: dict[str, Any]
    extreme_threshold_f: float
    elevated_threshold_f: float
    poll_interval_minutes: int
    manager_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
