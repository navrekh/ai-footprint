from aifootprint.models import AIModel, Methodology, Provider


def test_providers_list_returns_plain_list_not_wrapped(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/providers",
        json=[
            {
                "id": "openai",
                "name": "OpenAI",
                "status": "active",
                "supported_modalities": ["text", "image"],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ],
    )
    result = client.providers.list()
    assert isinstance(result, list)
    assert isinstance(result[0], Provider)
    assert result[0].id == "openai"
    # A bare list has no attribute to carry the request ID on - documented
    # exception, not an oversight.
    assert not hasattr(result, "request_id")


def test_models_list_with_filters(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/models?provider=openai&modality=text",
        json=[
            {
                "id": "model-id",
                "provider_id": "openai",
                "name": "Model One",
                "version": "2026-01-01",
                "modalities": ["text"],
                "status": "active",
                "methodology_version": "0.1",
                "effective_from": "2026-01-01",
                "effective_to": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ],
    )
    result = client.models.list(provider="openai", modality="text")
    assert isinstance(result, list)
    assert isinstance(result[0], AIModel)
    assert result[0].effective_to is None


def test_models_list_no_filters_sends_no_query_params(httpx_mock, client):
    httpx_mock.add_response(method="GET", url="http://testserver/v1/models", json=[])
    result = client.models.list()
    assert result == []
    request = httpx_mock.get_requests()[0]
    assert request.url.query == b""


def test_methodology_list(httpx_mock, client):
    httpx_mock.add_response(
        method="GET",
        url="http://testserver/v1/methodology",
        json=[
            {
                "id": "meth_1",
                "version": "0.1",
                "description": "TEST_ONLY methodology description.",
                "effective_date": "2026-01-01",
                "sources": ["source-a"],
                "assumptions": ["assumption-a"],
                "limitations": ["limitation-a"],
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
    )
    result = client.methodology.list()
    assert isinstance(result, list)
    assert isinstance(result[0], Methodology)
    assert result[0].limitations == ["limitation-a"]
