import pytest

from app.core.errors import InvalidWorkloadError
from app.methodology.validator import WorkloadValidator
from app.schemas.workload import WorkloadInput


def _workload(**overrides):
    defaults = {
        "provider": "openai",
        "model": "test-only-model",
        "modality": "text",
        "activity_type": "text_generation",
    }
    defaults.update(overrides)
    return WorkloadInput(**defaults)


def test_valid_text_workload_passes():
    WorkloadValidator().validate(_workload(input_tokens=100, output_tokens=50))


def test_zero_image_count_rejected():
    workload = _workload(modality="image", activity_type="image_generation", image_count=0)
    with pytest.raises(InvalidWorkloadError):
        WorkloadValidator().validate(workload)


def test_zero_video_seconds_rejected():
    workload = _workload(
        modality="video", activity_type="video_generation", video_seconds=0
    )
    with pytest.raises(InvalidWorkloadError):
        WorkloadValidator().validate(workload)


def test_zero_audio_seconds_rejected():
    workload = _workload(
        modality="audio", activity_type="audio_generation", audio_seconds=0
    )
    with pytest.raises(InvalidWorkloadError):
        WorkloadValidator().validate(workload)


def test_zero_tokens_both_sides_rejected():
    workload = _workload(input_tokens=0, output_tokens=0)
    with pytest.raises(InvalidWorkloadError):
        WorkloadValidator().validate(workload)


def test_activity_type_modality_mismatch_rejected_at_schema_level():
    with pytest.raises(ValueError):
        WorkloadInput(
            provider="openai",
            model="test-only-model",
            modality="text",
            activity_type="image_generation",
        )
