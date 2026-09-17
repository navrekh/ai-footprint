from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ProjectStatus
from app.models.ids import new_id

if TYPE_CHECKING:
    from app.models.api_key import ApiKey
    from app.models.organization import Organization


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_project_organization_slug"),
    )

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=partial(new_id, "proj")
    )
    organization_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ProjectStatus.ACTIVE.value
    )

    organization: Mapped["Organization"] = relationship(back_populates="projects")
    api_keys: Mapped[list["ApiKey"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
