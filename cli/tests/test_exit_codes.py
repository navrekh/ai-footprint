"""Every documented exit-code category (Sprint 7 FRD section 39.11) is
tested here exactly once, against the single centralized mapping
function - no command module is allowed to define its own.
"""

from __future__ import annotations

from aifootprint import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    TransportError,
    ValidationError,
)

from aifootprint_cli.exit_codes import (
    EXIT_AUTHENTICATION,
    EXIT_AUTHORIZATION,
    EXIT_CONFIGURATION_ERROR,
    EXIT_CONFLICT,
    EXIT_NOT_FOUND,
    EXIT_RATE_LIMITED,
    EXIT_SERVER_ERROR,
    EXIT_TRANSPORT_ERROR,
    EXIT_UNEXPECTED_ERROR,
    EXIT_VALIDATION,
    CliUsageError,
    ConfigurationError,
    exit_code_for,
)


def _api_error(cls):
    return cls("message", status_code=0, code="CODE", request_id="req_1")


def test_validation_error_maps_to_2():
    assert exit_code_for(_api_error(ValidationError)) == EXIT_VALIDATION


def test_cli_usage_error_also_maps_to_2():
    assert exit_code_for(CliUsageError("bad input")) == EXIT_VALIDATION


def test_authentication_error_maps_to_3():
    assert exit_code_for(_api_error(AuthenticationError)) == EXIT_AUTHENTICATION


def test_authorization_error_maps_to_4():
    assert exit_code_for(_api_error(AuthorizationError)) == EXIT_AUTHORIZATION


def test_not_found_error_maps_to_5():
    assert exit_code_for(_api_error(NotFoundError)) == EXIT_NOT_FOUND


def test_conflict_error_maps_to_6():
    assert exit_code_for(_api_error(ConflictError)) == EXIT_CONFLICT


def test_rate_limit_error_maps_to_7():
    assert exit_code_for(_api_error(RateLimitError)) == EXIT_RATE_LIMITED


def test_generic_api_error_maps_to_8():
    assert exit_code_for(_api_error(APIError)) == EXIT_SERVER_ERROR


def test_transport_error_maps_to_9():
    assert exit_code_for(TransportError("network down")) == EXIT_TRANSPORT_ERROR


def test_configuration_error_maps_to_10():
    assert exit_code_for(ConfigurationError("bad config")) == EXIT_CONFIGURATION_ERROR


def test_unexpected_exception_maps_to_the_documented_fallback():
    """A bug (e.g. a bare `KeyError`) must never silently reuse one of
    the documented 0/2-10 codes - it gets its own, separate fallback.
    """
    assert exit_code_for(KeyError("oops")) == EXIT_UNEXPECTED_ERROR


def test_fallback_code_is_not_one_of_the_documented_codes():
    documented = {
        0,
        EXIT_VALIDATION,
        EXIT_AUTHENTICATION,
        EXIT_AUTHORIZATION,
        EXIT_NOT_FOUND,
        EXIT_CONFLICT,
        EXIT_RATE_LIMITED,
        EXIT_SERVER_ERROR,
        EXIT_TRANSPORT_ERROR,
        EXIT_CONFIGURATION_ERROR,
    }
    assert EXIT_UNEXPECTED_ERROR not in documented


def test_every_documented_exit_code_is_unique():
    codes = [
        0,
        EXIT_VALIDATION,
        EXIT_AUTHENTICATION,
        EXIT_AUTHORIZATION,
        EXIT_NOT_FOUND,
        EXIT_CONFLICT,
        EXIT_RATE_LIMITED,
        EXIT_SERVER_ERROR,
        EXIT_TRANSPORT_ERROR,
        EXIT_CONFIGURATION_ERROR,
        EXIT_UNEXPECTED_ERROR,
    ]
    assert len(codes) == len(set(codes))
