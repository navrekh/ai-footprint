"""Registry resources - GET /v1/providers, GET /v1/models, and
GET /v1/methodology. All three are public (no API key required) and all
three return a bare JSON array, not a `{"items": [...], "total": ...}`
wrapper - the SDK mirrors that exactly and returns a plain `list`.

Because a plain `list` cannot carry extra attributes, these three calls
are the one documented exception to this SDK's usual `result.request_id`
convention (see models.ResultBase) - there is no top-level object to
attach it to. If you need the request ID for one of these specific
calls, none is exposed; every other SDK method still provides one.
"""

from __future__ import annotations

from ._transport import Transport
from .models import AIModel, Methodology, Provider


class ProvidersResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def list(self) -> list[Provider]:
        data, _request_id = self._transport.request("GET", "/v1/providers")
        return [Provider.model_validate(item) for item in data]


class ModelsResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        provider: str | None = None,
        modality: str | None = None,
        status: str | None = None,
    ) -> list[AIModel]:
        data, _request_id = self._transport.request(
            "GET",
            "/v1/models",
            params={"provider": provider, "modality": modality, "status": status},
        )
        return [AIModel.model_validate(item) for item in data]


class MethodologyResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def list(self) -> list[Methodology]:
        data, _request_id = self._transport.request("GET", "/v1/methodology")
        return [Methodology.model_validate(item) for item in data]
