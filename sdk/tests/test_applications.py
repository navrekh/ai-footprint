import json

from aifootprint.models import Application, ApplicationList


def _application_body(**overrides) -> dict:
    body = {
        "id": "app_1",
        "project_id": "proj_1",
        "name": "Support Bot",
        "slug": "support-bot",
        "description": None,
        "status": "active",
        "environment": "production",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    body.update(overrides)
    return body


def test_create(httpx_mock, client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/applications", json=_application_body()
    )
    result = client.applications.create(name="Support Bot", environment="production")

    request = httpx_mock.get_requests()[0]
    assert json.loads(request.content) == {"name": "Support Bot", "environment": "production"}
    assert isinstance(result, Application)
    assert result.id == "app_1"


def test_create_with_explicit_project_id_for_org_level_key(httpx_mock, client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/applications", json=_application_body()
    )
    client.applications.create(name="Support Bot", project_id="proj_1")
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["project_id"] == "proj_1"


def test_get(httpx_mock, client):
    httpx_mock.add_response(
        method="GET", url="http://testserver/v1/applications/app_1", json=_application_body()
    )
    result = client.applications.get("app_1")
    assert result.id == "app_1"


def test_list_with_project_filter_and_pagination(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/applications?project=proj_1&limit=25&offset=0",
        json={"items": [_application_body()], "total": 1},
    )
    result = client.applications.list(project_id="proj_1", limit=25, offset=0)
    assert isinstance(result, ApplicationList)
    assert result.total == 1


def test_update(httpx_mock, client):
    httpx_mock.add_response(
        method="PATCH",
        url="http://testserver/v1/applications/app_1",
        json=_application_body(status="inactive"),
    )
    result = client.applications.update("app_1", status="inactive")
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"status": "inactive"}
    assert result.status == "inactive"
