from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import ProviderStatus


class Provider(TimestampMixin, Base):
    """Provider registry entry.

    id is the stable, API-friendly slug (e.g. "openai") rather than an
    opaque generated id, per sprint brief section 9.
    """

    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ProviderStatus.ACTIVE.value
    )
    supported_modalities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
