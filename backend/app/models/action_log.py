"""SQLAlchemy model for alert action logs (voice + SMS dispatch records)."""

from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Uuid, func, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.worker import Worker
    from app.models.heat_snapshot import HeatSnapshot


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    heat_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("heat_snapshots.id", ondelete="SET NULL"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String, nullable=False)  # 'voice' | 'sms'
    provider_ref: Mapped[str | None] = mapped_column(String, nullable=True)  # CALL-E call_id or Twilio sid
    status: Mapped[str] = mapped_column(String, nullable=False, default="queued")
    transcript: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    worker: Mapped[Worker] = relationship("Worker", back_populates="action_logs")
    heat_snapshot: Mapped[HeatSnapshot | None] = relationship("HeatSnapshot", back_populates="action_logs")

    __table_args__ = (
        CheckConstraint("channel IN ('voice','sms')", name="ck_log_channel"),
        CheckConstraint("status IN ('queued','delivered','failed','acknowledged')", name="ck_log_status"),
        UniqueConstraint("worker_id", "heat_snapshot_id", "channel", name="uq_worker_snapshot_channel"),
        Index("idx_action_logs_cooldown", "worker_id", "channel", "status", "created_at"),
    )
