from datetime import datetime
from functools import partial

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow
from app.models.enums import MetricStatus
from app.models.ids import new_id


class Estimate(Base):
    """A persisted estimate is a self-contained provenance record.

    provider/model/model_version are denormalized from the resolved
    registry entries at calculation time (rather than requiring a join
    through workload_id) so that historical provenance survives even if
    a future sprint changes how AIWorkload stores these fields. They are
    nullable at the schema level only for migration safety; the service
    layer always populates them when persisting an estimate (see
    sprint review "Historical Immutability").
    """

    __tablename__ = "estimates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(new_id, "est"))
    workload_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("ai_workloads.id", ondelete="CASCADE"), nullable=False, index=True
    )

    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    energy_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MetricStatus.INSUFFICIENT_DATA.value
    )
    energy_min_wh: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_max_wh: Mapped[float | None] = mapped_column(Float, nullable=True)

    water_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MetricStatus.INSUFFICIENT_DATA.value
    )
    water_min_ml: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_max_ml: Mapped[float | None] = mapped_column(Float, nullable=True)

    carbon_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MetricStatus.INSUFFICIENT_DATA.value
    )
    carbon_min_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbon_max_g: Mapped[float | None] = mapped_column(Float, nullable=True)

    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    evidence_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accounting_boundary: Mapped[str | None] = mapped_column(String(4), nullable=True)

    methodology_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    assumptions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
