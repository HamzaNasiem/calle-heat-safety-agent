"""SQLAlchemy model for heat snapshots fetched from FortyGuard."""

from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Uuid, JSON, func, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.site import Site
    from app.models.action_log import ActionLog


class HeatSnapshot(Base):
    __tablename__ = "heat_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    fortyguard_activity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    temperature_f: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    analysis_layer: Mapped[str] = mapped_column(String, nullable=False, default="snapshot")
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    site: Mapped[Site] = relationship("Site", back_populates="heat_snapshots")
    action_logs: Mapped[list[ActionLog]] = relationship(
        "ActionLog",
        back_populates="heat_snapshot",
    )

    __table_args__ = (
        CheckConstraint("analysis_layer IN ('snapshot','exceedance','persistence')", name="ck_snapshot_layer"),
        CheckConstraint("risk_level IN ('normal','elevated','extreme')", name="ck_snapshot_risk"),
        Index("idx_snapshots_site_time", "site_id", "captured_at"),
    )
