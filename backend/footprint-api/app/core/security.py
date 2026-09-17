import hashlib
import secrets

_SECRET_BYTES = 32


def generate_api_key(prefix: str) -> tuple[str, str, str]:
    """Generate a new raw API key.

    Returns a tuple of (raw_key, key_hash, key_prefix).

    The raw key is returned exactly once to the caller and must never be
    persisted. Only its hash is stored at rest, per FRD section 6.
    """
    secret = secrets.token_urlsafe(_SECRET_BYTES)
    raw_key = f"{prefix}_{secret}"
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[: len(prefix) + 9]
    return raw_key, key_hash, key_prefix


def hash_api_key(raw_key: str) -> str:
    """Deterministically hash an API key for storage/lookup.

    API keys (unlike passwords) carry high entropy by construction, so a
    fast deterministic hash (SHA-256) used purely as a lookup/verification
    digest is appropriate here; a slow adaptive hash (bcrypt/scrypt) is
    unnecessary and would only slow down auth on every request.
    """
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
