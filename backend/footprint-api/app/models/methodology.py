from datetime import date, datetime
from functools import partial

from sqlalchemy import JSON, Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow
from app.models.ids import new_id


class Methodology(Base):
    """A published methodology version.

    Published methodology versions are immutable (FRD section 8) - the
    service layer must never update a row here once it exists; a change
    always creates a new version.
    """

    __tablename__ = "methodologies"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=partial(new_id, "methodology")
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    sources: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    assumptions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
