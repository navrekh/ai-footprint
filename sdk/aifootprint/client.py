"""The AI Footprint SDK's main entry point.

    from aifootprint import AIClient

    client = AIClient(api_key="afp_live_...")
    result = client.estimates.create(
        provider="openai",
        model="model-id",
        modality="text",
        activity_type="text_generation",
        input_tokens=2000,
        output_tokens=1000,
    )

`AIClient` owns one underlying HTTP connection (`httpx.Client`, via
`Transport`) shared by every resource namespace below. Close it when
done, or use it as a context manager.
"""

from __future__ import annotations

import os

from ._transport import Transport
from .api_keys import ApiKeysResource
from .applications import ApplicationsResource
from .batch import BatchResource
from .benchmarks import BenchmarksResource
from .compare import CompareResource
from .estimates import EstimatesResource
from .events import EventsResource
from .organizations import OrganizationsResource
from .projects import ProjectsResource
from .registry import MethodologyResource, ModelsResource, ProvidersResource
from .usage import UsageResource
from .workloads import WorkloadsResource

#: Local-development convenience default. There is no hosted AI
#: Footprint instance as of Sprint 5B (see docs/QUICKSTART.md) - real
#: usage should always set AIFOOTPRINT_BASE_URL or pass base_url=.
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 30.0

API_KEY_ENV_VAR = "AIFOOTPRINT_API_KEY"
BASE_URL_ENV_VAR = "AIFOOTPRINT_BASE_URL"


class AIClient:
    """Configuration precedence, for both `api_key` and `base_url`:

    1. the explicit constructor argument
    2. the corresponding environment variable
       (`AIFOOTPRINT_API_KEY` / `AIFOOTPRINT_BASE_URL`)
    3. a documented default (`base_url` only - `http://localhost:8000`;
       `api_key` has no default, since several endpoints, such as
       signing up and reading the public registries, require none)

    The API key is sent only as an `Authorization: Bearer <key>` header
    on every request - never as a query parameter, never in the URL,
    never logged, and never written to disk by this SDK.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        resolved_key = api_key or os.environ.get(API_KEY_ENV_VAR)
        resolved_base_url = (
            base_url or os.environ.get(BASE_URL_ENV_VAR) or DEFAULT_BASE_URL
        )

        self._transport = Transport(
            base_url=resolved_base_url, api_key=resolved_key, timeout=timeout
        )

        self.organizations = OrganizationsResource(self._transport)
        self.projects = ProjectsResource(self._transport)
        self.applications = ApplicationsResource(self._transport)
        self.api_keys = ApiKeysResource(self._transport)
        self.estimates = EstimatesResource(self._transport)
        self.events = EventsResource(self._transport)
        self.batch = BatchResource(self._transport)
        self.workloads = WorkloadsResource(self._transport)
        self.usage = UsageResource(self._transport)
        self.compare = CompareResource(self._transport)
        self.benchmarks = BenchmarksResource(self._transport)
        self.providers = ProvidersResource(self._transport)
        self.models = ModelsResource(self._transport)
        self.methodology = MethodologyResource(self._transport)

    def health(self) -> dict:
        """GET /health - public liveness check. Always returns
        `{"status": "ok"}`, with no request_id or wrapper (there's
        nothing else to preserve).
        """
        data, _request_id = self._transport.request("GET", "/health")
        return data

    def close(self) -> None:
        """Releases the underlying HTTP connection pool. Safe to call
        more than once.
        """
        self._transport.close()

    def __enter__(self) -> AIClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
