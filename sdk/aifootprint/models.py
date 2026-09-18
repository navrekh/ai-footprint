"""Typed models for the AI Footprint public API contract.

These models mirror the backend's actual response/request schemas
(``backend/footprint-api/app/schemas/*.py`` and the generated
``/openapi.json``) as of Sprint 5B. They intentionally do not include
every backend-internal field - only what the public REST API exposes.

Nothing here calculates, estimates, aggregates, or ranks anything. Every
field is either sent to the API verbatim or parsed from its response
verbatim. In particular:

* `min`/`max` ranges are never collapsed into an average or a single
  point value anywhere in this module.
* `status`/`confidence`/`coverage_percent`/`methodology_version`/
  `assumptions` fields are always preserved, never dropped.
* Comparison and benchmark results are plain lists in the order the API
  returned them - nothing here ranks, scores, or picks a "winner."
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums (mirror app/models/enums.py exactly - values only, no new taxonomy)
# ---------------------------------------------------------------------------


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODING = "coding"
    AGENT = "agent"
    OTHER = "other"


class ActivityType(str, Enum):
    TEXT_GENERATION = "text_generation"
    TEXT_REASONING = "text_reasoning"
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDITING = "image_editing"
    IMAGE_ENHANCEMENT = "image_enhancement"
    VIDEO_GENERATION = "video_generation"
    AUDIO_GENERATION = "audio_generation"
    SPEECH_TO_TEXT = "speech_to_text"
    VISION = "vision"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    TEST_GENERATION = "test_generation"
    CODE_REFACTORING = "code_refactoring"
    CODING_AGENT = "coding_agent"
    EMBEDDING = "embedding"
    RAG = "rag"
    CLASSIFICATION = "classification"
    AGENT_WORKFLOW = "agent_workflow"


class MetricStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    INSUFFICIENT_DATA = "insufficient_data"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NormalizationBasis(str, Enum):
    INPUT_PLUS_OUTPUT = "input_plus_output"
    IMAGE_COUNT = "image_count"
    VIDEO_SECONDS = "video_seconds"
    AUDIO_MINUTES = "audio_minutes"


class UsageGranularity(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ApplicationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ApplicationEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ClientType(str, Enum):
    """The software surface instrumenting a workload (Sprint 6). Purely
    observational - see ClientContext - and never affects the resulting
    estimate.
    """

    WEB = "web"
    PYTHON_SDK = "python_sdk"
    JAVASCRIPT_SDK = "javascript_sdk"
    CLI = "cli"
    BROWSER_EXTENSION = "browser_extension"
    IOS = "ios"
    ANDROID = "android"
    DIRECT_API = "direct_api"


# ---------------------------------------------------------------------------
# Base result - the single request-ID mechanism (see Sprint 5B Step 11).
# ---------------------------------------------------------------------------


class ResultBase(BaseModel):
    """Every top-level object an SDK call returns inherits from this.

    `request_id` is SDK-attached metadata (from the response's
    `X-Request-ID` header), not part of the backend's JSON body - it is
    excluded from `model_dump()`/serialization and is never required to
    construct an instance. This is the one, consistent place a caller
    finds the request ID for a successful call; failed calls carry the
    same value on the raised `APIError.request_id` instead (see
    exceptions.py) - there is no second mechanism.
    """

    model_config = ConfigDict(populate_by_name=True)

    request_id: str | None = Field(default=None, exclude=True, repr=False)


# ---------------------------------------------------------------------------
# Shared resource-intensity primitives (app/schemas/common.py)
# ---------------------------------------------------------------------------


class MetricRange(BaseModel):
    """A single metric's estimated range. `min`/`max` are never averaged
    into a point estimate by this SDK.
    """

    status: MetricStatus
    min: float | None = None
    max: float | None = None
    unit: str


class AggregateMetricRange(MetricRange):
    """A metric range aggregated across multiple workloads, with explicit
    completeness (`measured_workloads` out of `total_workloads`) - a
    partial aggregate is never indistinguishable from a complete one.
    """

    total_workloads: int
    measured_workloads: int


class ComparisonCandidate(BaseModel):
    provider: str
    model: str
    model_version: str | None = None


class ClientContext(BaseModel):
    """Identifies the software surface that instrumented a workload -
    distinct from `application_id`, which identifies the product/
    service/environment that *owns* the workload (Sprint 6). Every
    field is optional and observational only: this SDK does not, and
    the API contract does not, use any of these fields for estimation,
    authorization, or ownership. Submitting different client metadata
    for an otherwise identical workload never changes the resulting
    estimate.
    """

    client_type: ClientType | None = None
    client_name: str | None = None
    client_version: str | None = None
    integration_type: str | None = None
    integration_version: str | None = None
    runtime: str | None = None


class Denominator(BaseModel):
    """The workload quantity a normalized range was divided by - always
    present alongside a normalized value so the calculation is auditable.
    """

    value: float
    unit: str
    basis: NormalizationBasis


class NormalizedMetricRange(BaseModel):
    status: MetricStatus
    min: float | None = None
    max: float | None = None
    unit: str
    confidence: Confidence | None = None
    evidence_level: int | None = None
    methodology_version: str | None = None
    accounting_boundary: str | None = None


class NormalizedResourceIntensity(BaseModel):
    denominator: Denominator
    energy: NormalizedMetricRange | None = None
    water: NormalizedMetricRange | None = None
    carbon: NormalizedMetricRange | None = None


class ErrorDetail(BaseModel):
    """The shape of one failed candidate's error inside a comparison or
    benchmark result - distinct from an `APIError` raised for the overall
    HTTP call, since one candidate's failure never fails the whole call.
    """

    code: str
    message: str
    request_id: str


# ---------------------------------------------------------------------------
# Organizations / Projects / Applications / API keys
# ---------------------------------------------------------------------------


class Organization(ResultBase):
    id: str
    name: str
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime


class Project(ResultBase):
    id: str
    organization_id: str
    name: str
    slug: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectList(ResultBase):
    items: list[Project]
    total: int


class Application(ResultBase):
    id: str
    project_id: str
    name: str
    slug: str
    description: str | None
    status: str
    environment: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationList(ResultBase):
    items: list[Application]
    total: int


class ApiKeyCreated(ResultBase):
    """Returned exactly once, at creation time. The SDK never logs,
    prints, or persists the `key` field itself - see client.py.
    """

    id: str
    key: str
    key_prefix: str
    name: str


class ApiKey(ResultBase):
    """An API key as returned by list/revoke - never includes the raw
    key or its hash, only the display prefix.
    """

    id: str
    organization_id: str
    project_id: str | None
    key_prefix: str
    name: str
    status: str
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None


class ApiKeyList(ResultBase):
    items: list[ApiKey]
    total: int


class OrganizationBootstrap(ResultBase):
    """Returned by the signup call - the only place a raw API key is
    returned outside of creating an additional key explicitly.
    """

    organization: Organization
    project: Project
    api_key: ApiKeyCreated


# ---------------------------------------------------------------------------
# Estimates / Events / Batch / Workloads
# ---------------------------------------------------------------------------


class Estimate(ResultBase):
    """A stateless estimate (POST /v1/estimate, or one item of a batch).
    Nothing here is persisted server-side.
    """

    estimate_id: str
    energy: MetricRange
    water: MetricRange
    carbon: MetricRange
    confidence: Confidence | None
    evidence_level: int | None
    accounting_boundary: str | None
    methodology_version: str | None
    assumptions: list[str]
    created_at: datetime


class PersistedEstimate(ResultBase):
    """A durably-stored estimate (GET /v1/estimates/{id}), with the
    provenance fields that only exist once an estimate is persisted.
    """

    estimate_id: str
    workload_id: str
    provider: str | None
    model: str | None
    model_version: str | None
    energy: MetricRange
    water: MetricRange
    carbon: MetricRange
    confidence: Confidence | None
    evidence_level: int | None
    accounting_boundary: str | None
    methodology_version: str | None
    assumptions: list[str]
    status: str
    created_at: datetime


class Event(ResultBase):
    """Returned by POST /v1/events. `idempotent_replay` is true when this
    is the original result of an earlier call with the same
    idempotency_key, replayed rather than recomputed.
    """

    event_id: str
    workload_id: str
    estimate_id: str
    status: str
    idempotent_replay: bool = False


class Workload(ResultBase):
    id: str
    organization_id: str
    project_id: str
    application_id: str | None
    provider: str
    model: str
    model_version: str | None
    modality: str
    activity_type: str
    timestamp: datetime
    input_tokens: int | None
    output_tokens: int | None
    input_characters: int | None
    output_characters: int | None
    image_count: int | None
    image_width: int | None
    image_height: int | None
    video_seconds: float | None
    video_resolution: str | None
    audio_seconds: float | None
    tool_calls: int | None
    duration_seconds: float | None
    duration_ms: float | None
    parent_workload_id: str | None
    metadata: dict | None = None
    client: ClientContext | None = None
    created_at: datetime


class WorkloadPage(ResultBase):
    """Cursor-paginated (not limit/offset) workload history. Pass
    `next_cursor` back as `cursor` to fetch the next page; `None` means
    the last page.
    """

    items: list[Workload]
    next_cursor: str | None = None


class BatchItemResult(BaseModel):
    index: int
    status: str
    estimate: Estimate | None = None
    error: ErrorDetail | None = None


class AggregateImpact(BaseModel):
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class BatchResult(ResultBase):
    batch_id: str
    total_workloads: int
    successful_estimates: int
    failed_estimates: int
    aggregate_impact: AggregateImpact
    results: list[BatchItemResult]


# ---------------------------------------------------------------------------
# Usage intelligence
# ---------------------------------------------------------------------------


class UsagePeriod(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: datetime = Field(alias="from")
    to: datetime


class WorkloadCounts(BaseModel):
    """Coverage is always explicit: measured + partial + insufficient_data
    always sum to total, and coverage_percent is never silently rounded
    up to imply full coverage.
    """

    total: int
    measured: int
    partial: int
    insufficient_data: int
    coverage_percent: float


class UsageSummary(ResultBase):
    period: UsagePeriod
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageByProviderItem(BaseModel):
    provider: str
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageByProviderResult(ResultBase):
    period: UsagePeriod
    items: list[UsageByProviderItem]
    total: int


class UsageByModelItem(BaseModel):
    provider: str
    model: str
    model_version: str | None
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageByModelResult(ResultBase):
    period: UsagePeriod
    items: list[UsageByModelItem]
    total: int


class UsageByActivityItem(BaseModel):
    activity_type: str
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageByActivityResult(ResultBase):
    period: UsagePeriod
    items: list[UsageByActivityItem]
    total: int


class UsageByApplicationItem(BaseModel):
    application_id: str
    application_name: str
    project_id: str
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageByApplicationResult(ResultBase):
    period: UsagePeriod
    items: list[UsageByApplicationItem]
    total: int


class UsageTimeseriesPoint(BaseModel):
    period_start: datetime
    workloads: WorkloadCounts
    energy: AggregateMetricRange
    water: AggregateMetricRange
    carbon: AggregateMetricRange


class UsageTimeseriesResult(ResultBase):
    period: UsagePeriod
    granularity: str
    items: list[UsageTimeseriesPoint]


# ---------------------------------------------------------------------------
# Compare / Benchmarks (Sprint 4) - never ranked, scored, or reordered.
# ---------------------------------------------------------------------------


class ComparisonResultItem(BaseModel):
    """One candidate's independent outcome. This SDK returns these in
    exactly the order and shape the API provided - it never sorts,
    scores, or annotates a "winner."
    """

    candidate: ComparisonCandidate
    status: str
    resolved: ComparisonCandidate | None = None
    estimate: Estimate | None = None
    normalized: NormalizedResourceIntensity | None = None
    error: ErrorDetail | None = None


class CompareResult(ResultBase):
    comparison_id: str
    modality: str
    activity_type: str
    results: list[ComparisonResultItem]


class BenchmarkDefinition(ResultBase):
    benchmark_id: str
    version: str
    name: str
    description: str
    activity_type: str
    modality: str
    parameters: dict


class BenchmarkList(ResultBase):
    items: list[BenchmarkDefinition]
    total: int


class BenchmarkRunResult(ResultBase):
    benchmark_id: str
    benchmark_version: str
    modality: str
    activity_type: str
    results: list[ComparisonResultItem]


# ---------------------------------------------------------------------------
# Public registries (providers / models / methodology)
# ---------------------------------------------------------------------------


class Provider(BaseModel):
    id: str
    name: str
    status: str
    supported_modalities: list[str]
    created_at: datetime
    updated_at: datetime


class AIModel(BaseModel):
    """A registered provider/model entry. Named `AIModel` (not `Model`)
    to avoid confusion with "a Pydantic model" as a general term.
    """

    id: str
    provider_id: str
    name: str
    version: str | None
    modalities: list[str]
    status: str
    methodology_version: str | None
    effective_from: date | None
    effective_to: date | None
    created_at: datetime
    updated_at: datetime


class Methodology(BaseModel):
    id: str
    version: str
    description: str
    effective_date: date
    sources: list[str]
    assumptions: list[str]
    limitations: list[str]
    created_at: datetime
