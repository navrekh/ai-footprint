import pytest

ALLOWED_ORIGIN = "https://console.allowed.test"
BLOCKED_ORIGIN = "https://attacker.example"


@pytest.mark.asyncio
async def test_preflight_from_allowed_origin_is_permitted(client):
    response = await client.options(
        "/v1/providers",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


@pytest.mark.asyncio
async def test_preflight_from_blocked_origin_is_rejected(client):
    response = await client.options(
        "/v1/providers",
        headers={
            "Origin": BLOCKED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    # Starlette's CORSMiddleware answers a disallowed-origin preflight
    # with 400 and no Access-Control-Allow-Origin header - the browser
    # then refuses to send the real request. This is the "blocked" case:
    # no header naming the attacker's origin must ever be present.
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.asyncio
async def test_actual_request_from_allowed_origin_gets_cors_header(client, auth_headers):
    response = await client.get(
        "/v1/providers",
        headers={**auth_headers, "Origin": ALLOWED_ORIGIN},
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


@pytest.mark.asyncio
async def test_actual_request_from_blocked_origin_has_no_cors_header(client, auth_headers):
    response = await client.get(
        "/v1/providers",
        headers={**auth_headers, "Origin": BLOCKED_ORIGIN},
    )

    # The backend still answers (CORS is enforced by the browser, not the
    # server, for simple/actual requests) but must never claim the
    # attacker's origin is allowed.
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.asyncio
async def test_allowed_origin_401_response_still_carries_cors_header(client):
    """Regression guard: CORSMiddleware must wrap error responses too, not
    only 2xx ones. All prior tests in this file only ever observe CORS
    headers on a 200 response; if a future middleware-ordering change
    moved CORSMiddleware to wrap only the success path (e.g. placed
    inside the AppError exception handler instead of around it), a
    browser-based console would be unable to read the body of any error
    response from an otherwise-allowed origin - and nothing else in this
    suite would catch that.

    Also confirms CORS never bypasses authentication: an allowed origin
    with no Authorization header must still be rejected.
    """
    response = await client.get(
        "/v1/usage/summary",
        headers={"Origin": ALLOWED_ORIGIN},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


@pytest.mark.asyncio
async def test_blocked_origin_401_response_has_no_cors_header(client):
    response = await client.get(
        "/v1/usage/summary",
        headers={"Origin": BLOCKED_ORIGIN},
    )

    assert response.status_code == 401
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.asyncio
async def test_cors_never_enables_credentialed_requests(client):
    response = await client.options(
        "/v1/providers",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers.get("access-control-allow-credentials") != "true"


@pytest.mark.asyncio
async def test_cors_allows_only_the_documented_methods(client):
    response = await client.options(
        "/v1/providers",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "DELETE",
        },
    )

    # DELETE is not in the ADR-012 allowlist (GET/POST/PATCH/OPTIONS) -
    # Starlette rejects a preflight for a disallowed method.
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cors_allows_authorization_and_content_type_headers(client):
    response = await client.options(
        "/v1/compare",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in allowed_headers
    assert "content-type" in allowed_headers
