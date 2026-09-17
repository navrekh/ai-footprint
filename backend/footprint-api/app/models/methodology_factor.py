from datetime import date
from functools import partial

from sqlalchemy import JSON, Date, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.ids import new_id


class MethodologyFactor(TimestampMixin, Base):
    """A single versioned, sourced calculation factor.

    Factors are data, not application code (data/methodology/README.md).
    provider/model are plain nullable strings rather than foreign keys:
    the data contract explicitly allows generic factors with no provider
    or model (resolution precedence levels 3-5), and factors may target
    research/hardware scopes that do not correspond to a registered
    Provider/Model row.
    """

    __tablename__ = "methodology_factors"
    __table_args__ = (
        Index(
            "ix_methodology_factors_lookup",
            "metric",
            "provider",
            "model",
            "modality",
            "activity_type",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=partial(new_id, "factor")
    )
    factor_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    metric: Mapped[str] = mapped_column(String(16), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    modality: Mapped[str] = mapped_column(String(16), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hardware: Mapped[str | None] = mapped_column(String(128), nullable=True)

    value_min: Mapped[float] = mapped_column(Float, nullable=False)
    value_max: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)

    evidence_level: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)

    source: Mapped[str] = mapped_column(String, nullable=False)
    source_date: Mapped[date] = mapped_column(Date, nullable=False)

    accounting_boundary: Mapped[str] = mapped_column(String(4), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    methodology_version: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    assumptions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
