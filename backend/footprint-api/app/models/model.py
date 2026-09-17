from datetime import date
from functools import partial

from sqlalchemy import JSON, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import ModelStatus
from app.models.ids import new_id


class Model(TimestampMixin, Base):
    __tablename__ = "models"
    __table_args__ = (
        UniqueConstraint("provider_id", "name", "version", name="uq_model_provider_name_version"),
    )

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=partial(new_id, "model")
    )
    provider_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    modalities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ModelStatus.ACTIVE.value
    )
    methodology_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
