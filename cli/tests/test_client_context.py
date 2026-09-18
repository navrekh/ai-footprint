"""Sprint 6 client-metadata generation (Sprint 7 FRD section 39.14):
every CLI event identifies itself as `client_type=cli`, with the
installed CLI version and a non-sensitive runtime identifier - and
nothing here is capable of influencing authorization or estimation
(it produces a plain data object, nothing more).
"""

from __future__ import annotations

import platform

from aifootprint import ClientType

from aifootprint_cli import __version__
from aifootprint_cli.context import CLIENT_NAME, build_client_context


def test_client_type_is_cli():
    context = build_client_context()
    assert context.client_type == ClientType.CLI


def test_client_name_is_the_documented_constant():
    context = build_client_context()
    assert context.client_name == "aifootprint-cli"
    assert context.client_name == CLIENT_NAME


def test_client_version_matches_the_single_source_of_truth():
    context = build_client_context()
    assert context.client_version == __version__


def test_runtime_is_a_non_sensitive_python_version_identifier():
    context = build_client_context()
    assert context.runtime == f"python/{platform.python_version()}"
    # Never a full sys.version string (which can include compiler/build
    # host details) - just the bare version number.
    assert "[" not in context.runtime


def test_client_context_carries_no_authorization_fields():
    """Structural guarantee: ClientContext has no organization/project/
    application/API-key field at all, so it cannot be mistaken for
    authorization data by construction, not just by convention.
    """
    context = build_client_context()
    dumped = context.model_dump()
    forbidden = {"organization_id", "project_id", "application_id", "api_key", "key"}
    assert forbidden.isdisjoint(dumped.keys())
