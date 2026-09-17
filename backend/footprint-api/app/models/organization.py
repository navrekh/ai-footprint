from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import OrganizationStatus
from app.models.ids import new_id

if TYPE_CHECKING:
    from app.models.project import Project


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=partial(new_id, "org")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=OrganizationStatus.ACTIVE.value
    )

    projects: Mapped[list["Project"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
