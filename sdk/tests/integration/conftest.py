"""Fixtures for integration tests that exercise the SDK against a real,
locally running instance of the backend (Sprint 5B, Step 15).

These tests are opt-in (`pytest -m integration`) and skipped by the
default test run (see `[tool.pytest.ini_options] addopts` in pyproject.toml)
because they require:

- a local Postgres reachable at `SDK_INTEGRATION_DATABASE_URL` (defaults
  to a dedicated `footprint_sdk_integration_test` database - deliberately
  NOT the backend's own `footprint_test`, since these tests commit real
  rows through real HTTP requests rather than rolling back in a
  per-test transaction, and must never pollute the backend's own
  test suite), and
- the backend's own virtualenv (to run `alembic upgrade head`, the seed
  script, and `uvicorn`) at `../../backend/footprint-api/.venv`.

Nothing here is a dependency of the shipped `aifootprint` package - this
is dev/test-only tooling that happens to also know where the backend
repo lives, for the sole purpose of standing it up as a real server.
"""

from __future__ import annotations

import os
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[3] / "backend" / "footprint-api"
BACKEND_VENV_PYTHON = BACKEND_DIR / ".venv" / "bin" / "python"

TEST_DATABASE_URL = os.environ.get(
    "SDK_INTEGRATION_DATABASE_URL",
    "postgresql+asyncpg://footprint:footprint@localhost:5432/footprint_sdk_integration_test",
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _ensure_database_exists(async_database_url: str) -> None:
    """Mirrors the backend's own `tests/conftest.py::_ensure_test_database`
    so this fixture is self-contained and never touches the backend's
    database - creating a fresh, dedicated one instead if it doesn't
    already exist.

    Runs as a subprocess using the backend's venv (which has `psycopg`)
    rather than importing it here - the SDK's own venv intentionally has
    no Postgres driver, since the shipped SDK never talks to a database
    directly.
    """
    sync_url = async_database_url.replace("postgresql+asyncpg", "postgresql")
    parts = urlsplit(sync_url)
    db_name = parts.path.lstrip("/")
    admin_url = urlunsplit((parts.scheme, parts.netloc, "/postgres", "", ""))

    script = (
        "import psycopg\n"
        f"conn = psycopg.connect({admin_url!r}, autocommit=True)\n"
        "with conn.cursor() as cur:\n"
        f"    cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', ({db_name!r},))\n"
        "    if cur.fetchone() is None:\n"
        f"        cur.execute('CREATE DATABASE \"{db_name}\"')\n"
        "conn.close()\n"
    )
    result = subprocess.run(
        [str(BACKEND_VENV_PYTHON), "-c", script], capture_output=True, text=True
    )
    if result.returncode != 0:
        pytest.fail(f"Could not ensure database {db_name!r} exists:\n{result.stderr}")


def _backend_env() -> dict[str, str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL
    env["ENVIRONMENT"] = "test"
    env["API_KEY_PREFIX"] = "afp_test"
    return env


def _wait_until_healthy(base_url: str, process: subprocess.Popen, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Backend process exited early with code {process.returncode} - "
                "see stderr above for the actual startup failure."
            )
        try:
            response = httpx.get(f"{base_url}/health", timeout=1.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    raise TimeoutError(f"Backend at {base_url} did not become healthy within {timeout}s")


@pytest.fixture(scope="session")
def live_backend_url() -> Iterator[str]:
    if not BACKEND_VENV_PYTHON.exists():
        pytest.skip(
            f"Backend virtualenv not found at {BACKEND_VENV_PYTHON} - integration tests "
            "require the backend's own venv to run migrations, seed data, and uvicorn."
        )

    env = _backend_env()
    _ensure_database_exists(TEST_DATABASE_URL)

    migrate = subprocess.run(
        [str(BACKEND_VENV_PYTHON), "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    if migrate.returncode != 0:
        pytest.fail(f"alembic upgrade head failed:\n{migrate.stdout}\n{migrate.stderr}")

    seed = subprocess.run(
        [str(BACKEND_VENV_PYTHON), "scripts/seed.py", "--with-test-only-demo-data"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    if seed.returncode != 0:
        pytest.fail(f"seed.py failed:\n{seed.stdout}\n{seed.stderr}")

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [
            str(BACKEND_VENV_PYTHON),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_until_healthy(base_url, process)
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@pytest.fixture(scope="session")
def bootstrapped_org(live_backend_url: str):
    """A fresh organization/project/API key, created once per test session
    via the SDK's own bootstrap call - so these tests never share mutable
    state with the backend's own `Demo Organization` seed data.
    """
    from aifootprint import AIClient

    with AIClient(base_url=live_backend_url) as anon_client:
        bootstrap = anon_client.organizations.create(
            name=f"SDK Integration Test Org {os.getpid()}-{int(time.time())}"
        )
    return bootstrap


@pytest.fixture()
def client(live_backend_url: str, bootstrapped_org):
    from aifootprint import AIClient

    with AIClient(api_key=bootstrapped_org.api_key.key, base_url=live_backend_url) as c:
        yield c
