from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.methodology import Methodology


class MethodologyResolver:
    """Pipeline stage 4: resolves the published Methodology metadata record
    referenced by the resolved model's methodology_version.

    A missing methodology is a valid, expected outcome (an
    insufficient-data state), not an application error - so this returns
    None rather than raising.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def resolve(self, methodology_version: str | None) -> Methodology | None:
        if not methodology_version:
            return None
        result = await self._db.execute(
            select(Methodology).where(Methodology.version == methodology_version)
        )
        return result.scalar_one_or_none()
