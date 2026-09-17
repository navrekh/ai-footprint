import base64
import binascii
from datetime import datetime

from app.core.errors import InvalidRequestError

_SEPARATOR = "|"


def encode_cursor(created_at: datetime, row_id: str) -> str:
    raw = f"{created_at.isoformat()}{_SEPARATOR}{row_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        created_at_raw, row_id = raw.split(_SEPARATOR, 1)
        return datetime.fromisoformat(created_at_raw), row_id
    except (ValueError, binascii.Error) as exc:
        raise InvalidRequestError("Invalid pagination cursor.") from exc
