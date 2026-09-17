from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db_session
from app.core.errors import UnauthorizedError
from app.services.auth_service import AuthContext, AuthService


async def get_auth_context(
    request: Request, db: AsyncSession = Depends(get_db_session)
) -> AuthContext:
    """Resolves Authorization: Bearer <API_KEY> -> Project -> Organization
    for a protected endpoint (FRD section 18).
    """
    header = request.headers.get("Authorization")
    if not header or not header.strip():
        raise UnauthorizedError("Missing Authorization header.")

    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise UnauthorizedError("Authorization header must be in the form 'Bearer <API_KEY>'.")

    return await AuthService(db).authenticate(parts[1].strip())
