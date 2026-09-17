from abc import ABC, abstractmethod
from typing import Any


class ProviderAdapter(ABC):
    """Normalizes provider-specific request telemetry into the canonical
    AIWorkload representation (ARCHITECTURE.md section 7).

    Sprint 1 adapters do not call any provider API - their purpose is to
    prove the extensibility boundary so the Footprint Engine never needs
    provider-specific branching. A future sprint that adds real ingestion
    fills in `normalize` without touching the estimation pipeline.
    """

    provider_id: str

    @abstractmethod
    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Map provider-specific telemetry fields onto canonical AIWorkload fields."""
        raise NotImplementedError


class OpenAIAdapter(ProviderAdapter):
    provider_id = "openai"

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return dict(raw)


class AnthropicAdapter(ProviderAdapter):
    provider_id = "anthropic"

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return dict(raw)


class GoogleAdapter(ProviderAdapter):
    provider_id = "google"

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return dict(raw)
