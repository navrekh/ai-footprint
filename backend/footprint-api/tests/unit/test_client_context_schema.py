"""Sprint 6 - schema-level tests for the client/integration metadata
contract (app/schemas/workload.py:ClientContext, app/models/enums.py:
ClientType). These exercise Pydantic validation directly, with no HTTP
layer, database, or estimation pipeline involved.
"""

import pytest
from pydantic import ValidationError

from app.models.enums import ClientType
from app.schemas.workload import ClientContext, EventCreateRequest, WorkloadInput

BASE_WORKLOAD = {
    "provider": "openai",
    "model": "model-id",
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 2000,
    "output_tokens": 1000,
}


def test_workload_input_accepts_full_client_metadata():
    workload = WorkloadInput(
        **BASE_WORKLOAD,
        client={
            "client_type": "python_sdk",
            "client_name": "aifootprint-python",
            "client_version": "0.5.0",
            "integration_type": "backend_middleware",
            "integration_version": "1.2.0",
            "runtime": "python/3.13",
        },
    )
    assert workload.client is not None
    assert workload.client.client_type == ClientType.PYTHON_SDK
    assert workload.client.client_name == "aifootprint-python"
    assert workload.client.client_version == "0.5.0"
    assert workload.client.integration_type == "backend_middleware"
    assert workload.client.integration_version == "1.2.0"
    assert workload.client.runtime == "python/3.13"


def test_client_metadata_is_entirely_optional():
    """Omitting `client` entirely - the pre-Sprint-6 shape - must keep
    working unchanged. This is the core backward-compatibility guarantee.
    """
    workload = WorkloadInput(**BASE_WORKLOAD)
    assert workload.client is None

    event = EventCreateRequest(**BASE_WORKLOAD)
    assert event.client is None


@pytest.mark.parametrize("client_type", list(ClientType))
def test_every_supported_client_type_is_accepted(client_type: ClientType):
    workload = WorkloadInput(**BASE_WORKLOAD, client={"client_type": client_type.value})
    assert workload.client.client_type == client_type


def test_invalid_client_type_is_rejected():
    with pytest.raises(ValidationError):
        WorkloadInput(**BASE_WORKLOAD, client={"client_type": "not_a_real_client_type"})


def test_client_name_cannot_exceed_maximum_length():
    with pytest.raises(ValidationError):
        ClientContext(client_name="x" * 129)


def test_client_name_at_maximum_length_is_accepted():
    ClientContext(client_name="x" * 128)


@pytest.mark.parametrize(
    "field", ["client_name", "client_version", "integration_type", "integration_version", "runtime"]
)
def test_empty_string_is_rejected_for_every_bounded_field(field: str):
    with pytest.raises(ValidationError):
        ClientContext(**{field: ""})


def test_client_context_alone_with_every_field_omitted_is_valid():
    context = ClientContext()
    assert context.client_type is None
    assert context.client_name is None
    assert context.client_version is None
    assert context.integration_type is None
    assert context.integration_version is None
    assert context.runtime is None


def test_backward_compatible_existing_request_shape_still_validates():
    """The exact request shape used before Sprint 6 - no `client` key at
    all in the JSON payload - must still validate identically.
    """
    workload = WorkloadInput.model_validate(BASE_WORKLOAD)
    assert workload.client is None
    assert workload.provider == "openai"
