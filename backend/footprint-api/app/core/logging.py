import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_REDACTED_KEYS = {
    "api_key",
    "authorization",
    "key_hash",
    "raw_key",
    "password",
    "secret",
    "prompt",
    "content",
}


class JSONLogFormatter(logging.Formatter):
    """Structured JSON log formatter.

    Never emits API keys, secrets, prompts or generated content (FRD
    section 27). Callers pass request-scoped metadata via the `extra=`
    kwarg on the stdlib logger; any key matching a redacted name is
    dropped defensively before it can reach a log line.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _REDACTED_KEYS:
                continue
            if key in (
                "args",
                "msg",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "name",
                "message",
                "taskName",
            ):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(log_level: str) -> None:
    root = logging.getLogger()
    root.setLevel(log_level.upper())
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONLogFormatter())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
