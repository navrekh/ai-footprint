from enum import StrEnum


class Modality(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODING = "coding"
    AGENT = "agent"
    OTHER = "other"


class ActivityType(StrEnum):
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
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


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

