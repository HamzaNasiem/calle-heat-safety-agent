"""SQLAlchemy model for site workers."""

from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Uuid, func, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.site import Site
    from app.models.action_log import ActionLog


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String, nullable=False, default="en")
    consented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="safe",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    site: Mapped[Site] = relationship("Site", back_populates="workers")
    action_logs: Mapped[list[ActionLog]] = relationship(
        "ActionLog",
        back_populates="worker",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("status IN ('safe','elevated','notified','acknowledged')", name="ck_worker_status"),
        Index("idx_workers_site", "site_id"),
        Index("idx_workers_site_consented", "site_id", "consented_at"),
    )
