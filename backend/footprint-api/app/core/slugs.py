import re
import secrets

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(value: str, *, fallback: str = "item") -> str:
    """Convert a display name into a URL-safe slug base.

    Uniqueness is not handled here - callers combine this with a
    collision check (and a short random suffix on collision) against the
    relevant scope (globally for organizations, per-organization for
    projects).
    """
    slug = _NON_ALNUM.sub("-", value.strip().lower()).strip("-")
    return slug or fallback


def with_unique_suffix(slug: str) -> str:
    return f"{slug}-{secrets.token_hex(3)}"
