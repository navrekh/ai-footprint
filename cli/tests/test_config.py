"""Configuration precedence (Sprint 7 FRD section 39.9): explicit CLI
option > environment variable > local configuration file > SDK/default.
"""

from __future__ import annotations

import json
import os
import stat

import pytest

from aifootprint_cli.config import (
    config_file_path,
    resolve_api_key,
    resolve_base_url,
)
from aifootprint_cli.exit_codes import ConfigurationError


def _write_config(data: dict) -> None:
    path = config_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_missing_configuration_resolves_to_none():
    assert resolve_api_key(None) is None
    assert resolve_base_url(None) is None


def test_cli_option_wins_over_everything(monkeypatch):
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", "from-env")
    _write_config({"api_key": "from-config"})

    assert resolve_api_key("from-cli") == "from-cli"


def test_env_var_wins_over_local_config(monkeypatch):
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", "from-env")
    _write_config({"api_key": "from-config"})

    assert resolve_api_key(None) == "from-env"


def test_local_config_used_when_cli_and_env_are_absent():
    _write_config({"api_key": "from-config", "base_url": "http://from-config:9000"})

    assert resolve_api_key(None) == "from-config"
    assert resolve_base_url(None) == "http://from-config:9000"


def test_no_configuration_anywhere_falls_through_to_none():
    """The CLI never invents its own default - it returns None and lets
    AIClient apply its own documented default/behavior.
    """
    assert resolve_api_key(None) is None
    assert resolve_base_url(None) is None


def test_malformed_local_config_raises_configuration_error():
    path = config_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not valid json")

    with pytest.raises(ConfigurationError):
        resolve_api_key(None)


def test_local_config_that_is_not_a_json_object_raises_configuration_error():
    path = config_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[1, 2, 3]")

    with pytest.raises(ConfigurationError):
        resolve_api_key(None)


def test_empty_string_in_local_config_is_treated_as_absent():
    _write_config({"api_key": ""})
    assert resolve_api_key(None) is None


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission bits only")
def test_group_or_world_readable_config_emits_a_warning(capsys):
    _write_config({"api_key": "from-config"})
    config_file_path().chmod(0o644)

    resolve_api_key(None)

    captured = capsys.readouterr()
    assert "readable by other users" in captured.err


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission bits only")
def test_owner_only_permissions_emit_no_warning(capsys):
    _write_config({"api_key": "from-config"})
    config_file_path().chmod(stat.S_IRUSR | stat.S_IWUSR)

    resolve_api_key(None)

    captured = capsys.readouterr()
    assert "readable by other users" not in captured.err
