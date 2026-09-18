"""The CLI's centralized process exit-code contract (Sprint 7 FRD
section 39.11). Every command dispatch goes through `exit_code_for()`
exactly once (see cli.py's `main()`) - no command module maps its own
exceptions to a process exit code.
"""

from __future__ import annotations

from aifootprint import (
    AIFootprintError,
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    TransportError,
    ValidationError,
)

EXIT_SUCCESS = 0
EXIT_VALIDATION = 2
EXIT_AUTHENTICATION = 3
EXIT_AUTHORIZATION = 4
EXIT_NOT_FOUND = 5
EXIT_CONFLICT = 6
EXIT_RATE_LIMITED = 7
EXIT_SERVER_ERROR = 8
EXIT_TRANSPORT_ERROR = 9
EXIT_CONFIGURATION_ERROR = 10

#: Documented fallback for a genuinely unexpected (programming) error -
#: deliberately NOT one of the 0/2-10 codes above, so a bug can never be
#: mistaken for one of the documented categories by a script branching
#: on exit code.
EXIT_UNEXPECTED_ERROR = 1


class CliUsageError(Exception):
    """A CLI-side input problem detected before any API call is made
    (e.g. malformed --metadata JSON, a malformed --candidate value).
    Maps to the same exit code as an API-side ValidationError (2) -
    both represent invalid input from the caller's perspective, just
    caught at a different layer.
    """


class ConfigurationError(Exception):
    """A CLI-level configuration problem - e.g. an unreadable or
    malformed local configuration file (see config.py). Distinct from
    ValidationError/CliUsageError: this is about *resolving* how to
    call the API, not about the workload/request content itself.
    """


def exit_code_for(exc: BaseException) -> int:
    """The one place an exception is translated into a process exit
    code. Order matters: every SDK exception class checked here is a
    subclass of APIError except AIFootprintError/TransportError, so the
    more specific checks must run before the general APIError fallback.
    """
    if isinstance(exc, CliUsageError):
        return EXIT_VALIDATION
    if isinstance(exc, ConfigurationError):
        return EXIT_CONFIGURATION_ERROR
    if isinstance(exc, AuthenticationError):
        return EXIT_AUTHENTICATION
    if isinstance(exc, AuthorizationError):
        return EXIT_AUTHORIZATION
    if isinstance(exc, NotFoundError):
        return EXIT_NOT_FOUND
    if isinstance(exc, ValidationError):
        return EXIT_VALIDATION
    if isinstance(exc, ConflictError):
        return EXIT_CONFLICT
    if isinstance(exc, RateLimitError):
        return EXIT_RATE_LIMITED
    if isinstance(exc, TransportError):
        return EXIT_TRANSPORT_ERROR
    if isinstance(exc, APIError):
        return EXIT_SERVER_ERROR
    if isinstance(exc, AIFootprintError):
        return EXIT_SERVER_ERROR
    return EXIT_UNEXPECTED_ERROR
