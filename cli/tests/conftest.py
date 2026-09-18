"""Shared CLI test fixtures.

Unit/contract tests intercept HTTP the same way the SDK's own unit
tests do: `httpx_mock` (pytest-httpx) patches the transport underneath
`AIClient` regardless of which package instantiated it, so these tests
prove the CLI reaches the SDK's real `httpx.Client` - never a second,
CLI-specific HTTP path.
"""

from __future__ import annotations

import os

import pytest

BASE_URL = "http://testserver"


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path, monkeypatch):
    """Every test starts with a clean slate: no inherited
    AIFOOTPRINT_API_KEY/AIFOOTPRINT_BASE_URL from the developer's own
    shell, and its own throwaway XDG_CONFIG_HOME so local-configuration
    tests never read or write the real `~/.config/aifootprint`.
    """
    monkeypatch.delenv("AIFOOTPRINT_API_KEY", raising=False)
    monkeypatch.delenv("AIFOOTPRINT_BASE_URL", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    os.makedirs(tmp_path / "home", exist_ok=True)
    yield


@pytest.fixture
def api_env(monkeypatch):
    """A minimal, valid environment so a command can reach the (mocked)
    API without needing --api-key/--base-url on every invocation.
    """
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", "afp_test_key")
    monkeypatch.setenv("AIFOOTPRINT_BASE_URL", BASE_URL)
