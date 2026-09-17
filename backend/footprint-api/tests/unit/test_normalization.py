from app.methodology.dto import MetricEstimate
from app.methodology.normalization import normalize_metric, resolve_denominator
from app.models.enums import Confidence, MetricStatus, Modality, NormalizationBasis
from app.schemas.workload import WorkloadInput


def _workload(**overrides) -> WorkloadInput:
    defaults = dict(
        provider="openai",
        model="test-only-model",
        modality=Modality.TEXT,
        activity_type="text_generation",
    )
    defaults.update(overrides)
    return WorkloadInput(**defaults)


def test_text_denominator_uses_input_plus_output_tokens():
    workload = _workload(input_tokens=400, output_tokens=600)

    denominator = resolve_denominator(workload)

    assert denominator is not None
    assert denominator.basis == NormalizationBasis.INPUT_PLUS_OUTPUT
    assert denominator.value == 1.0  # 1000 tokens / 1000
    assert denominator.unit == "1K tokens"


def test_image_denominator_uses_image_count():
    workload = _workload(
        modality=Modality.IMAGE, activity_type="image_generation", image_count=4
    )

    denominator = resolve_denominator(workload)

    assert denominator is not None
    assert denominator.basis == NormalizationBasis.IMAGE_COUNT
    assert denominator.value == 4.0
    assert denominator.unit == "image"


def test_video_denominator_uses_video_seconds():
    workload = _workload(
        modality=Modality.VIDEO, activity_type="video_generation", video_seconds=10.0
    )

    denominator = resolve_denominator(workload)

    assert denominator is not None
    assert denominator.basis == NormalizationBasis.VIDEO_SECONDS
    assert denominator.value == 10.0
    assert denominator.unit == "second"


def test_audio_denominator_converts_seconds_to_minutes():
    workload = _workload(
        modality=Modality.AUDIO, activity_type="audio_generation", audio_seconds=120.0
    )

    denominator = resolve_denominator(workload)

    assert denominator is not None
    assert denominator.basis == NormalizationBasis.AUDIO_MINUTES
    assert denominator.value == 2.0
    assert denominator.unit == "minute"


def test_unsupported_denominator_is_none():
    workload = _workload(
        modality=Modality.AGENT, activity_type="agent_workflow", tool_calls=3
    )

    assert resolve_denominator(workload) is None


def test_zero_quantity_does_not_produce_a_denominator():
    workload = _workload(input_tokens=0, output_tokens=0, image_count=0)

    assert resolve_denominator(workload) is None


def test_missing_quantity_fields_produce_no_denominator():
    workload = _workload()

    assert resolve_denominator(workload) is None


def test_normalize_metric_divides_min_and_max_independently():
    metric = MetricEstimate(
        status=MetricStatus.OK,
        unit="Wh",
        min=1.0,
        max=2.0,
        confidence=Confidence.MEDIUM,
        evidence_level=3,
        accounting_boundary="A",
    )
    denominator = resolve_denominator(_workload(input_tokens=1000, output_tokens=1000))
    assert denominator is not None
    assert denominator.value == 2.0  # 2000 tokens / 1000

    normalized = normalize_metric(metric, "0.1", denominator)

    assert normalized.min == 0.5  # 1.0 Wh / 2.0 (1K tokens)
    assert normalized.max == 1.0  # 2.0 Wh / 2.0 (1K tokens)
    assert normalized.unit == "Wh per 1K tokens"


def test_normalize_metric_preserves_status_confidence_and_provenance():
    metric = MetricEstimate(
        status=MetricStatus.OK,
        unit="Wh",
        min=1.0,
        max=2.0,
        confidence=Confidence.HIGH,
        evidence_level=1,
        accounting_boundary="B",
    )
    denominator = resolve_denominator(_workload(input_tokens=1000, output_tokens=0))
    assert denominator is not None

    normalized = normalize_metric(metric, "2.3", denominator)

    assert normalized.status == MetricStatus.OK
    assert normalized.confidence == Confidence.HIGH
    assert normalized.evidence_level == 1
    assert normalized.accounting_boundary == "B"
    assert normalized.methodology_version == "2.3"


def test_normalize_metric_insufficient_data_stays_insufficient_data_not_zero():
    metric = MetricEstimate(status=MetricStatus.INSUFFICIENT_DATA, unit="Wh")
    denominator = resolve_denominator(_workload(input_tokens=500, output_tokens=500))
    assert denominator is not None

    normalized = normalize_metric(metric, None, denominator)

    assert normalized.status == MetricStatus.INSUFFICIENT_DATA
    assert normalized.min is None
    assert normalized.max is None


def test_normalize_metric_never_produces_a_single_point_value():
    metric = MetricEstimate(status=MetricStatus.OK, unit="Wh", min=1.0, max=3.0)
    denominator = resolve_denominator(_workload(input_tokens=1000, output_tokens=0))
    assert denominator is not None

    normalized = normalize_metric(metric, "0.1", denominator)

    # Both bounds preserved independently - never collapsed to (min+max)/2.
    assert normalized.min != normalized.max
    assert normalized.min == 1.0
    assert normalized.max == 3.0
