from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ApplicationStatus
from app.models.ids import new_id

if TYPE_CHECKING:
    from app.models.project import Project


class Application(TimestampMixin, Base):
    """A specific AI product, service, environment or workload source
    belonging to exactly one project (PRD/FRD v0.2 domain hierarchy:
    Organization -> Project -> Application -> AIWorkload).
    """

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_application_project_slug"),
    )

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=partial(new_id, "app")
    )
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ApplicationStatus.ACTIVE.value
    )
    environment: Mapped[str | None] = mapped_column(String(16), nullable=True)

    project: Mapped["Project"] = relationship()
