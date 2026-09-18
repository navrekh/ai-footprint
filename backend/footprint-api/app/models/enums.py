from enum import StrEnum


class Modality(StrEnum):
    """The general category of workload being measured.

    * `text` - conversational/text-generation and reasoning workloads.
    * `image` - image generation, editing, enhancement, and vision analysis.
    * `video` - video generation workloads.
    * `audio` - speech-to-text and audio generation workloads.
    * `coding` - code generation, review, debugging, refactoring, and test generation.
    * `agent` - multi-step autonomous agent workflows and coding-agent sessions.
    * `other` - workloads (e.g. embeddings, RAG, classification) that are not
      inherently tied to one of the modalities above.
    """

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODING = "coding"
    AGENT = "agent"
    OTHER = "other"


class ActivityType(StrEnum):
    """The specific kind of AI operation a workload represents.

    Each activity_type is only valid under specific modalities (enforced at
    request-validation time - see ACTIVITY_TYPE_MODALITIES below):

    * `text_generation` - conversational text generation (modality: `text`).
    * `text_reasoning` - multi-step reasoning over text (modality: `text`).
    * `image_generation` - generating a new image (modality: `image`).
    * `image_editing` - modifying an existing image (modality: `image`).
    * `image_enhancement` - upscaling/enhancing an existing image (modality: `image`).
    * `video_generation` - generating a video (modality: `video`).
    * `audio_generation` - generating audio/speech (modality: `audio`).
    * `speech_to_text` - transcribing audio to text (modality: `audio`).
    * `vision` - analyzing/describing an image (modality: `image`).
    * `code_generation` - generating new code (modality: `coding`).
    * `code_review` - reviewing existing code (modality: `coding`).
    * `debugging` - diagnosing/fixing a defect (modality: `coding`).
    * `test_generation` - generating tests (modality: `coding`).
    * `code_refactoring` - restructuring code without changing behavior (modality: `coding`).
    * `coding_agent` - an autonomous coding-agent step (modality: `coding` or `agent`).
    * `embedding` - generating a vector embedding (modality: `text` or `other`).
    * `rag` - retrieval-augmented generation (modality: `text` or `other`).
    * `classification` - classifying text/image content (modality: `text`, `image`, or `other`).
    * `agent_workflow` - a step within a general multi-step autonomous agent (modality: `agent`).
    """

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


# Maps each activity type to the modality(ies) it is valid under. Used only
# for request-level semantic validation - it carries no environmental
# calculation meaning and must never be treated as one.
ACTIVITY_TYPE_MODALITIES: dict[ActivityType, set[Modality]] = {
    ActivityType.TEXT_GENERATION: {Modality.TEXT},
    ActivityType.TEXT_REASONING: {Modality.TEXT},
    ActivityType.IMAGE_GENERATION: {Modality.IMAGE},
    ActivityType.IMAGE_EDITING: {Modality.IMAGE},
    ActivityType.IMAGE_ENHANCEMENT: {Modality.IMAGE},
    ActivityType.VIDEO_GENERATION: {Modality.VIDEO},
    ActivityType.AUDIO_GENERATION: {Modality.AUDIO},
    ActivityType.SPEECH_TO_TEXT: {Modality.AUDIO},
    ActivityType.VISION: {Modality.IMAGE},
    ActivityType.CODE_GENERATION: {Modality.CODING},
    ActivityType.CODE_REVIEW: {Modality.CODING},
    ActivityType.DEBUGGING: {Modality.CODING},
    ActivityType.TEST_GENERATION: {Modality.CODING},
    ActivityType.CODE_REFACTORING: {Modality.CODING},
    ActivityType.CODING_AGENT: {Modality.CODING, Modality.AGENT},
    ActivityType.EMBEDDING: {Modality.TEXT, Modality.OTHER},
    ActivityType.RAG: {Modality.TEXT, Modality.OTHER},
    ActivityType.CLASSIFICATION: {Modality.TEXT, Modality.IMAGE, Modality.OTHER},
    ActivityType.AGENT_WORKFLOW: {Modality.AGENT},
}


def validate_activity_type_modality(activity_type: ActivityType, modality: Modality) -> None:
    """The single authoritative activity_type/modality compatibility check.

    Raises ValueError on an incompatible pair. Shared by WorkloadInput
    (app/schemas/workload.py), CompareRequest (app/schemas/compare.py) and
    the methodology validator (scripts/validate_methodology.py) so there
    is exactly one taxonomy compatibility rule in the codebase, never a
    second copy of it.
    """
    allowed = ACTIVITY_TYPE_MODALITIES.get(activity_type)
    if allowed is not None and modality not in allowed:
        raise ValueError(
            f"activity_type '{activity_type}' is not valid for modality '{modality}'"
        )


class ProviderStatus(StrEnum):
    ACTIVE = "active"
    BETA = "beta"
    DEPRECATED = "deprecated"


class ModelStatus(StrEnum):
    ACTIVE = "active"
    BETA = "beta"
    DEPRECATED = "deprecated"


class ApiKeyStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ApplicationStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ApplicationEnvironment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class EventMeasurementStatus(StrEnum):
    """Overall completeness of a persisted event's estimate, derived from
    its per-metric statuses (never itself stored - see
    workload_service.compute_event_status).
    """

    MEASURED = "measured"
    PARTIAL = "partial"
    INSUFFICIENT_DATA = "insufficient_data"


class Metric(StrEnum):
    ENERGY = "energy"
    WATER = "water"
    CARBON = "carbon"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Ordering from weakest to strongest, used when combining confidence
# across multiple metrics/factors (the combined confidence is never
# stronger than its weakest contributing factor).
CONFIDENCE_ORDER: dict[Confidence, int] = {
    Confidence.LOW: 0,
    Confidence.MEDIUM: 1,
    Confidence.HIGH: 2,
}


class AccountingBoundary(StrEnum):
    """See docs/METHODOLOGY.md section 3."""

    A = "A"  # AI inference operations only
    B = "B"  # + data-center operational footprint
    C = "C"  # + lifecycle/embodied footprint (not used in MVP)


class MetricStatus(StrEnum):
    OK = "ok"
    PARTIAL = "partial"
    INSUFFICIENT_DATA = "insufficient_data"


class UsageGranularity(StrEnum):
    """The time-bucket size for `GET /v1/usage/timeseries`.

    * `day` - one bucket per calendar day.
    * `week` - one bucket per calendar week.
    * `month` - one bucket per calendar month.

    A wider date range combined with a finer granularity may be rejected
    with `INVALID_DATE_RANGE` if it would exceed the maximum bucket count.
    """

    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ClientType(StrEnum):
    """The software surface that instrumented a workload (Sprint 6 FRD
    section 38.3). Purely observational - see WorkloadInput.client - and
    must never influence provider/model resolution, methodology
    resolution, or the resulting estimate.

    * `web` - the AI Footprint developer console.
    * `python_sdk` - the official Python SDK.
    * `javascript_sdk` - a future JavaScript/TypeScript SDK.
    * `cli` - a future command-line client.
    * `browser_extension` - a future browser extension.
    * `ios` - a future iOS application.
    * `android` - a future Android application.
    * `direct_api` - a caller integrating directly against the REST API,
      without any of the above.
    """

    WEB = "web"
    PYTHON_SDK = "python_sdk"
    JAVASCRIPT_SDK = "javascript_sdk"
    CLI = "cli"
    BROWSER_EXTENSION = "browser_extension"
    IOS = "ios"
    ANDROID = "android"
    DIRECT_API = "direct_api"


class NormalizationBasis(StrEnum):
    """The workload quantity a normalized resource-intensity range was
    divided by (docs/METHODOLOGY.md section 25). Always returned alongside
    a normalized value so the calculation is auditable rather than
    implicit.
    """

    INPUT_PLUS_OUTPUT = "input_plus_output"
    IMAGE_COUNT = "image_count"
    VIDEO_SECONDS = "video_seconds"
    AUDIO_MINUTES = "audio_minutes"

