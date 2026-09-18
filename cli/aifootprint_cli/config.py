"""CLI configuration resolution (Sprint 7 FRD section 39.9).

Precedence for both `api_key` and `base_url`:

    1. an explicit CLI option (--api-key / --base-url)
    2. an environment variable (AIFOOTPRINT_API_KEY / AIFOOTPRINT_BASE_URL)
    3. a local, user-local configuration file
    4. the SDK's own default behavior (AIClient itself already falls
       back to its environment-variable check, then its documented
       localhost default for base_url, and no default for api_key -
       see sdk/aifootprint/client.py) - this module never duplicates
       that default; it simply returns None when nothing more specific
       was found, and lets AIClient apply it.

This module never performs an HTTP request and never talks to the SDK
directly - it only resolves plain strings, which cli.py then passes to
`AIClient(api_key=..., base_url=...)`.
"""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

from .exit_codes import ConfigurationError

API_KEY_ENV_VAR = "AIFOOTPRINT_API_KEY"
BASE_URL_ENV_VAR = "AIFOOTPRINT_BASE_URL"

#: Bits that, if set, mean "readable/writable by someone other than the
#: file's owner" - the same threshold `ssh` warns about for private keys.
_GROUP_OR_WORLD_ACCESS = stat.S_IRWXG | stat.S_IRWXO


def config_dir() -> Path:
    """User-local, honoring XDG_CONFIG_HOME when set (Linux convention)
    and falling back to `~/.config/aifootprint` otherwise, which also
    works on macOS. No secrets-manager integration in Sprint 7 - see
    the CLI README's "Configuration" section for the documented,
    intentionally minimal scope.
    """
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "aifootprint"


def config_file_path() -> Path:
    return config_dir() / "config.json"


def load_local_config() -> dict:
    """Returns `{}` when the file simply does not exist - that is the
    normal, expected case for most invocations, not an error. A file
    that exists but cannot be read or parsed raises `ConfigurationError`
    (exit code 10) rather than being silently ignored, so a typo in a
    hand-edited config file is never mistaken for "no key configured."
    """
    path = config_file_path()
    if not path.exists():
        return {}

    _warn_if_permissions_too_open(path)

    try:
        raw = path.read_text()
    except OSError as exc:
        raise ConfigurationError(f"Could not read configuration file {path}: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Configuration file {path} is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigurationError(f"Configuration file {path} must contain a JSON object.")
    return data


def _warn_if_permissions_too_open(path: Path) -> None:
    """Best-effort, POSIX-only (Windows' permission model does not map
    onto these bits - `os.name` guards this so the check is simply
    skipped there, per FRD 39.9's "where supported"). Never raises:
    an unreadable-mode stat() failure is surfaced by the subsequent
    `read_text()` call instead.
    """
    if os.name != "posix":
        return
    try:
        mode = path.stat().st_mode
    except OSError:
        return
    if mode & _GROUP_OR_WORLD_ACCESS:
        print(
            f"Warning: {path} is readable by other users on this system. "
            f"Run 'chmod 600 {path}' to restrict access to your API key.",
            file=sys.stderr,
        )


def resolve_api_key(cli_value: str | None) -> str | None:
    if cli_value:
        return cli_value
    env_value = os.environ.get(API_KEY_ENV_VAR)
    if env_value:
        return env_value
    local_value = load_local_config().get("api_key")
    return local_value if isinstance(local_value, str) and local_value else None


def resolve_base_url(cli_value: str | None) -> str | None:
    if cli_value:
        return cli_value
    env_value = os.environ.get(BASE_URL_ENV_VAR)
    if env_value:
        return env_value
    local_value = load_local_config().get("base_url")
    return local_value if isinstance(local_value, str) and local_value else None
