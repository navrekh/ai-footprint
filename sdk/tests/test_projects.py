import json

from aifootprint.models import Project, ProjectList


def _project_body(**overrides) -> dict:
    body = {
        "id": "proj_1",
        "organization_id": "org_1",
        "name": "Production",
        "slug": "production",
        "description": "Production workloads",
        "status": "active",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    body.update(overrides)
    return body


def test_create(httpx_mock, client):
    httpx_mock.add_response(
        method="POST", url="http://testserver/v1/projects", json=_project_body()
    )
    result = client.projects.create(name="Production", description="Production workloads")

    request = httpx_mock.get_requests()[0]
    assert request.method == "POST"
    assert json.loads(request.content) == {
        "name": "Production",
        "description": "Production workloads",
    }
    assert isinstance(result, Project)
    assert result.id == "proj_1"


def test_get(httpx_mock, client):
    httpx_mock.add_response(
        method="GET", url="http://testserver/v1/projects/proj_1", json=_project_body()
    )
    result = client.projects.get("proj_1")
    assert httpx_mock.get_requests()[0].url.path == "/v1/projects/proj_1"
    assert result.id == "proj_1"


def test_list_sends_limit_and_offset_query_params(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/projects?limit=10&offset=20",
        json={"items": [_project_body()], "total": 1},
    )
    result = client.projects.list(limit=10, offset=20)
    assert isinstance(result, ProjectList)
    assert result.total == 1
    assert len(result.items) == 1
    assert isinstance(result.items[0], Project)


def test_list_default_pagination(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/projects?limit=50&offset=0",
        json={"items": [], "total": 0},
    )
    result = client.projects.list()
    assert result.items == []
    assert result.total == 0


def test_update_sends_patch_with_only_provided_fields(httpx_mock, client):
    httpx_mock.add_response(
        method="PATCH",
        url="http://testserver/v1/projects/proj_1",
        json=_project_body(status="archived"),
    )
    result = client.projects.update("proj_1", status="archived")

    request = httpx_mock.get_requests()[0]
    assert request.method == "PATCH"
    # name/description omitted entirely - the transport drops None values,
    # never sending {"name": null, ...} for fields the caller did not set.
    assert json.loads(request.content) == {"status": "archived"}
    assert result.status == "archived"
