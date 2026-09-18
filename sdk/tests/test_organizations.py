from aifootprint.models import Organization, OrganizationBootstrap


def _bootstrap_body() -> dict:
    return {
        "organization": {
            "id": "org_1",
            "name": "Acme Inc",
            "slug": "acme-inc",
            "status": "active",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
        "project": {
            "id": "proj_1",
            "organization_id": "org_1",
            "name": "Default Project",
            "slug": "default-project",
            "description": None,
            "status": "active",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
        "api_key": {
            "id": "key_1",
            "key": "afp_live_rawkeyvalue",
            "key_prefix": "afp_live_raw",
            "name": "Default Key",
        },
    }


def test_create_sends_correct_method_path_and_body_without_auth(httpx_mock, unauthenticated_client):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/organizations",
        json=_bootstrap_body(),
        headers={"X-Request-ID": "req_1"},
    )
    result = unauthenticated_client.organizations.create(name="Acme Inc")

    request = httpx_mock.get_requests()[0]
    assert request.method == "POST"
    assert request.url.path == "/v1/organizations"
    assert "authorization" not in request.headers
    import json

    assert json.loads(request.content) == {"name": "Acme Inc"}

    assert isinstance(result, OrganizationBootstrap)
    assert result.organization.id == "org_1"
    assert result.project.id == "proj_1"
    assert result.api_key.key == "afp_live_rawkeyvalue"
    assert result.request_id == "req_1"


def test_create_result_does_not_serialize_request_id(httpx_mock, unauthenticated_client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/organizations", json=_bootstrap_body()
    )
    result = unauthenticated_client.organizations.create(name="Acme Inc")
    assert "request_id" not in result.model_dump()


def test_get_sends_correct_method_and_path(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/organizations/org_1",
        json={
            "id": "org_1",
            "name": "Acme Inc",
            "slug": "acme-inc",
            "status": "active",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
        headers={"X-Request-ID": "req_2"},
    )
    result = client.organizations.get("org_1")

    request = httpx_mock.get_requests()[0]
    assert request.method == "GET"
    assert request.url.path == "/v1/organizations/org_1"
    assert request.headers["authorization"] == "Bearer afp_test_key"

    assert isinstance(result, Organization)
    assert result.id == "org_1"
    assert result.request_id == "req_2"
