import re
import secrets
from collections.abc import Awaitable, Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_errors import is_unique_violation

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_DEFAULT_MAX_LENGTH = 255
_SUFFIX_HEX_BYTES = 3  # secrets.token_hex(3) -> 6 hex chars
MAX_SLUG_ALLOCATION_ATTEMPTS = 5


def slugify(value: str, *, fallback: str = "item") -> str:
    """Convert a display name into a URL-safe slug base.

    Uniqueness is not handled here - use allocate_unique_slug, which
    treats the database constraint as the actual authority rather than
    a pre-insert check.
    """
    slug = _NON_ALNUM.sub("-", value.strip().lower()).strip("-")
    return slug or fallback


def with_unique_suffix(slug: str, *, max_length: int = _DEFAULT_MAX_LENGTH) -> str:
    """Appends a short random suffix, truncating the base slug so the
    result never exceeds max_length (the slug column width). Without
    this, a duplicate name that is already at the column limit would
    overflow it once suffixed and fail with an unhandled database error
    (sprint 2 follow-up review).
    """
    suffix = f"-{secrets.token_hex(_SUFFIX_HEX_BYTES)}"
    budget = max(max_length - len(suffix), 1)
    return f"{slug[:budget]}{suffix}"


async def allocate_unique_slug[T](
    db: AsyncSession,
    *,
    name: str,
    fallback: str,
    constraint_name: str,
    try_insert: Callable[[str], Awaitable[T]],
) -> T:
    """Generates a slug from name and retries with a fresh random suffix
    whenever try_insert raises a unique violation for constraint_name.

    The database is the actual authority on uniqueness, not whatever
    candidate looked free a moment earlier - a concurrent request can
    commit the same candidate between when it is chosen and when it is
    inserted (sprint 2 follow-up review). Each attempt runs inside its
    own SAVEPOINT (begin_nested) so a failed attempt only undoes that
    attempt, never anything already staged earlier in the caller's
    transaction. Any IntegrityError that is not this specific
    constraint is re-raised unchanged, never retried.

    try_insert must persist a candidate (e.g. add() + flush() the row)
    and return whatever the caller wants back (typically the persisted
    ORM object); on success, allocate_unique_slug returns that value.
    """
    base = slugify(name, fallback=fallback)
    candidate = base
    for _ in range(MAX_SLUG_ALLOCATION_ATTEMPTS):
        try:
            async with db.begin_nested():
                result = await try_insert(candidate)
            return result
        except IntegrityError as exc:
            if not is_unique_violation(exc, constraint_name):
                raise
            candidate = with_unique_suffix(base)
    raise RuntimeError(f"Could not allocate a unique slug for {fallback!r} after retries.")
