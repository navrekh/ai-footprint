from app.providers.base import AnthropicAdapter, GoogleAdapter, OpenAIAdapter, ProviderAdapter

_ADAPTERS: dict[str, type[ProviderAdapter]] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "google": GoogleAdapter,
}


def get_adapter(provider_id: str) -> ProviderAdapter | None:
    adapter_cls = _ADAPTERS.get(provider_id)
    return adapter_cls() if adapter_cls else None


def register_adapter(provider_id: str, adapter_cls: type[ProviderAdapter]) -> None:
    """Adding a new provider requires registering an adapter here - never
    modifying the Footprint Engine (ARCHITECTURE.md section 17).
    """
    _ADAPTERS[provider_id] = adapter_cls
