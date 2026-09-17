from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow
from app.models.ids import new_id

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.project import Project


class AIWorkload(Base):
    """The canonical domain object (ARCHITECTURE.md section 2 / FRD section 2).

    Only rows created via POST /v1/events are persisted here - /v1/estimate
    and /v1/batch-estimate are stateless calculate-only endpoints (see
    README "Architecture notes" for the reasoning).
    """

    __tablename__ = "ai_workloads"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(new_id, "evt"))
    organization_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    modality: Mapped[str] = mapped_column(String(16), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    image_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    video_seconds: Mapped[float | None] = mapped_column(nullable=True)
    video_resolution: Mapped[str | None] = mapped_column(String(32), nullable=True)

    audio_seconds: Mapped[float | None] = mapped_column(nullable=True)

    tool_calls: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)

    parent_workload_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("ai_workloads.id", ondelete="SET NULL"), nullable=True, index=True
    )

    workload_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    organization: Mapped["Organization"] = relationship()
    project: Mapped["Project"] = relationship()
    children: Mapped[list["AIWorkload"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped["AIWorkload | None"] = relationship(
        back_populates="children", remote_side="AIWorkload.id"
    )
