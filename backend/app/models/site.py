"""SQLAlchemy model for registered work sites."""

from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, Uuid, JSON, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.manager import Manager
    from app.models.worker import Worker
    from app.models.heat_snapshot import HeatSnapshot


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("managers.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    polygon_geojson: Mapped[dict] = mapped_column(JSON, nullable=False)
    extreme_threshold_f: Mapped[float] = mapped_column(Numeric, nullable=False, default=110)
    elevated_threshold_f: Mapped[float] = mapped_column(Numeric, nullable=False, default=100)
    poll_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    manager: Mapped[Manager | None] = relationship("Manager", back_populates="sites")
    workers: Mapped[list[Worker]] = relationship(
        "Worker",
        back_populates="site",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    heat_snapshots: Mapped[list[HeatSnapshot]] = relationship(
        "HeatSnapshot",
        back_populates="site",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
