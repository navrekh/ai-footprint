import httpx
import pytest

from aifootprint.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    TransportError,
    ValidationError,
)


def _error_body(code: str, message: str = "boom", request_id: str = "req_xyz") -> dict:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


@pytest.mark.parametrize(
    ("status_code", "code", "expected_exc"),
    [
        (400, "INVALID_REQUEST", ValidationError),
        (400, "MISSING_PARAMETER", ValidationError),
        (400, "INVALID_DATE_RANGE", ValidationError),
        (401, "UNAUTHORIZED", AuthenticationError),
        (401, "INVALID_API_KEY", AuthenticationError),
        (401, "API_KEY_EXPIRED", AuthenticationError),
        (403, "FORBIDDEN", AuthorizationError),
        (404, "NOT_FOUND", NotFoundError),
        (404, "PROVIDER_NOT_FOUND", NotFoundError),
        (404, "APPLICATION_NOT_FOUND", NotFoundError),
        (404, "BENCHMARK_NOT_FOUND", NotFoundError),
        (409, "CONFLICT", ConflictError),
        (422, "MODEL_NOT_SUPPORTED", ValidationError),
        (422, "INVALID_WORKLOAD", ValidationError),
        (422, "APPLICATION_PROJECT_MISMATCH", ValidationError),
        (429, "RATE_LIMITED", RateLimitError),
        (500, "INTERNAL_ERROR", APIError),
        (503, "UNKNOWN", APIError),
    ],
)
def test_status_code_maps_to_expected_exception_type(
    httpx_mock, client, status_code, code, expected_exc
):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/providers",
        status_code=status_code,
        json=_error_body(code),
    )
    with pytest.raises(expected_exc) as exc_info:
        client.providers.list()
    err = exc_info.value
    assert err.status_code == status_code
    assert err.code == code
    assert err.message == "boom"
    assert err.request_id == "req_xyz"


def test_api_error_str_includes_diagnostics(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/providers",
        status_code=404,
        json=_error_body("NOT_FOUND", message="Resource not found.", request_id="req_123"),
    )
    with pytest.raises(NotFoundError) as exc_info:
        client.providers.list()
    text = str(exc_info.value)
    assert "Resource not found." in text
    assert "404" in text
    assert "NOT_FOUND" in text
    assert "req_123" in text


def test_error_response_never_leaks_authorization_header_value(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/providers",
        status_code=401,
        json=_error_body("INVALID_API_KEY", message="The provided API key is invalid or revoked."),
    )
    with pytest.raises(AuthenticationError) as exc_info:
        client.providers.list()
    assert "afp_test_key" not in str(exc_info.value)


def test_non_json_error_response_still_raises_api_error(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/providers",
        status_code=500,
        content=b"<html>Internal Server Error</html>",
        headers={"content-type": "text/html"},
    )
    with pytest.raises(APIError) as exc_info:
        client.providers.list()
    assert exc_info.value.status_code == 500


def test_network_error_raises_transport_error(httpx_mock, client):
    httpx_mock.add_exception(httpx.ConnectError("connection refused"))
    with pytest.raises(TransportError):
        client.providers.list()


def test_timeout_raises_transport_error(httpx_mock, client):
    httpx_mock.add_exception(httpx.ReadTimeout("timed out"))
    with pytest.raises(TransportError):
        client.providers.list()


def test_request_id_extracted_from_header_on_success(httpx_mock, client):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/estimate",
        json=_estimate_body(),
        headers={"X-Request-ID": "req_success123"},
    )
    result = client.estimates.create(
        provider="openai",
        model="model-id",
        modality="text",
        activity_type="text_generation",
        input_tokens=100,
        output_tokens=50,
    )
    assert result.request_id == "req_success123"


def test_request_id_from_header_used_when_body_omits_it(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/providers",
        status_code=404,
        json={"error": {"code": "NOT_FOUND", "message": "gone"}},
        headers={"X-Request-ID": "req_from_header"},
    )
    with pytest.raises(NotFoundError) as exc_info:
        client.providers.list()
    assert exc_info.value.request_id == "req_from_header"


def _estimate_body() -> dict:
    return {
        "estimate_id": "est_abc",
        "energy": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "Wh"},
        "water": {"status": "ok", "min": 0.1, "max": 0.2, "unit": "mL"},
        "carbon": {"status": "ok", "min": 0.01, "max": 0.02, "unit": "gCO2e"},
        "confidence": "medium",
        "evidence_level": 3,
        "accounting_boundary": "B",
        "methodology_version": "0.1",
        "assumptions": [],
        "created_at": "2026-01-01T00:00:00Z",
    }
