import httpx
import pytest

from aifootprint import AIClient
from aifootprint.client import BASE_URL_ENV_VAR, DEFAULT_BASE_URL, DEFAULT_TIMEOUT_SECONDS


def test_explicit_api_key_is_used(httpx_mock):
    client = AIClient(api_key="explicit-key", base_url="http://testserver")
    httpx_mock.add_response(method="GET", url="http://testserver/health", json={"status": "ok"})
    client.health()
    request = httpx_mock.get_requests()[0]
    assert request.headers["authorization"] == "Bearer explicit-key"
    client.close()


def test_api_key_from_environment_variable(monkeypatch, httpx_mock):
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", "env-key")
    client = AIClient(base_url="http://testserver")
    httpx_mock.add_response(method="GET", url="http://testserver/health", json={"status": "ok"})
    client.health()
    request = httpx_mock.get_requests()[0]
    assert request.headers["authorization"] == "Bearer env-key"
    client.close()


def test_explicit_api_key_takes_precedence_over_environment(monkeypatch, httpx_mock):
    monkeypatch.setenv("AIFOOTPRINT_API_KEY", "env-key")
    client = AIClient(api_key="explicit-key", base_url="http://testserver")
    httpx_mock.add_response(method="GET", url="http://testserver/health", json={"status": "ok"})
    client.health()
    request = httpx_mock.get_requests()[0]
    assert request.headers["authorization"] == "Bearer explicit-key"
    client.close()


def test_no_api_key_omits_authorization_header(httpx_mock):
    client = AIClient(base_url="http://testserver")
    httpx_mock.add_response(method="GET", url="http://testserver/health", json={"status": "ok"})
    client.health()
    request = httpx_mock.get_requests()[0]
    assert "authorization" not in request.headers
    client.close()


def test_explicit_base_url_is_used(httpx_mock):
    client = AIClient(api_key="k", base_url="http://custom-host:1234")
    httpx_mock.add_response(
        method="GET", url="http://custom-host:1234/health", json={"status": "ok"}
    )
    client.health()
    client.close()


def test_base_url_from_environment_variable(monkeypatch, httpx_mock):
    monkeypatch.setenv(BASE_URL_ENV_VAR, "http://env-host:5555")
    client = AIClient(api_key="k")
    httpx_mock.add_response(method="GET", url="http://env-host:5555/health", json={"status": "ok"})
    client.health()
    client.close()


def test_explicit_base_url_takes_precedence_over_environment(monkeypatch, httpx_mock):
    monkeypatch.setenv(BASE_URL_ENV_VAR, "http://env-host:5555")
    client = AIClient(api_key="k", base_url="http://explicit-host:9999")
    httpx_mock.add_response(
        method="GET", url="http://explicit-host:9999/health", json={"status": "ok"}
    )
    client.health()
    client.close()


def test_default_base_url_is_documented_local_default(monkeypatch):
    monkeypatch.delenv(BASE_URL_ENV_VAR, raising=False)
    client = AIClient(api_key="k")
    assert client._transport._client.base_url == httpx.URL(DEFAULT_BASE_URL)
    client.close()


def test_default_timeout_is_applied():
    client = AIClient(api_key="k", base_url="http://testserver")
    assert client._transport._client.timeout.read == DEFAULT_TIMEOUT_SECONDS
    client.close()


def test_custom_timeout_is_applied():
    client = AIClient(api_key="k", base_url="http://testserver", timeout=5.0)
    assert client._transport._client.timeout.read == 5.0
    client.close()


def test_close_releases_the_http_client():
    client = AIClient(api_key="k", base_url="http://testserver")
    client.close()
    assert client._transport._client.is_closed


def test_close_is_idempotent():
    client = AIClient(api_key="k", base_url="http://testserver")
    client.close()
    client.close()  # must not raise


def test_context_manager_closes_on_exit():
    with AIClient(api_key="k", base_url="http://testserver") as client:
        assert not client._transport._client.is_closed
    assert client._transport._client.is_closed


def test_context_manager_closes_on_exception():
    with pytest.raises(ValueError):
        with AIClient(api_key="k", base_url="http://testserver") as client:
            raise ValueError("boom")
    assert client._transport._client.is_closed


def test_api_key_is_never_in_repr_or_str():
    client = AIClient(api_key="super-secret-key", base_url="http://testserver")
    assert "super-secret-key" not in repr(client)
    assert "super-secret-key" not in str(client)
    client.close()
