"""Sprint 6 client-context generation for CLI-submitted events (Sprint 7
FRD section 39.4/39.14). Uses the SDK's own `ClientContext`/`ClientType`
models - there is no CLI-specific representation of this metadata.

This is observational only: nothing in cli.py, commands/, or the SDK
ever reads this metadata back to make an authorization, ownership, or
estimation decision (see the Sprint 6 regression tests in
backend/footprint-api/tests/integration/test_client_instrumentation.py
for the backend-side guarantee this relies on).
"""

from __future__ import annotations

import platform

from aifootprint import ClientContext, ClientType

from . import __version__

CLIENT_NAME = "aifootprint-cli"


def build_client_context() -> ClientContext:
    return ClientContext(
        client_type=ClientType.CLI,
        client_name=CLIENT_NAME,
        client_version=__version__,
        runtime=f"python/{platform.python_version()}",
    )
