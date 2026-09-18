import json

from aifootprint.models import ApiKey, ApiKeyCreated, ApiKeyList


def test_create_returns_raw_key_exactly_once(httpx_mock, client):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/api-keys",
        json={
            "id": "key_2",
            "key": "afp_live_brandnewrawkey",
            "key_prefix": "afp_live_bran",
            "name": "CI Key",
        },
    )
    result = client.api_keys.create(name="CI Key", project_id="proj_1")

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"name": "CI Key", "project_id": "proj_1"}
    assert isinstance(result, ApiKeyCreated)
    assert result.key == "afp_live_brandnewrawkey"


def test_list_never_exposes_raw_key(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/api-keys?limit=50&offset=0",
        json={
            "items": [
                {
                    "id": "key_1",
                    "organization_id": "org_1",
                    "project_id": "proj_1",
                    "key_prefix": "afp_live_bran",
                    "name": "CI Key",
                    "status": "active",
                    "created_at": "2026-01-01T00:00:00Z",
                    "expires_at": None,
                    "last_used_at": None,
                    "revoked_at": None,
                }
            ],
            "total": 1,
        },
    )
    result = client.api_keys.list()
    assert isinstance(result, ApiKeyList)
    key = result.items[0]
    assert isinstance(key, ApiKey)
    assert not hasattr(key, "key")  # ApiKey (list/revoke shape) has no raw-key field at all


def test_revoke(httpx_mock, client):
    httpx_mock.add_response(
        method="POST",
        url="http://testserver/v1/api-keys/key_1/revoke",
        json={
            "id": "key_1",
            "organization_id": "org_1",
            "project_id": "proj_1",
            "key_prefix": "afp_live_bran",
            "name": "CI Key",
            "status": "revoked",
            "created_at": "2026-01-01T00:00:00Z",
            "expires_at": None,
            "last_used_at": None,
            "revoked_at": "2026-01-02T00:00:00Z",
        },
    )
    result = client.api_keys.revoke("key_1")
    assert httpx_mock.get_requests()[0].url.path == "/v1/api-keys/key_1/revoke"
    assert result.status == "revoked"
