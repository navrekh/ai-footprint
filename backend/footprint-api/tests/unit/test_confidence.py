from app.methodology.confidence import ConfidenceEngine
from app.models.enums import Confidence


def test_from_evidence_level_mapping():
    assert ConfidenceEngine.from_evidence_level(1) == Confidence.HIGH
    assert ConfidenceEngine.from_evidence_level(2) == Confidence.HIGH
    assert ConfidenceEngine.from_evidence_level(3) == Confidence.MEDIUM
    assert ConfidenceEngine.from_evidence_level(4) == Confidence.MEDIUM
    assert ConfidenceEngine.from_evidence_level(5) == Confidence.LOW
    assert ConfidenceEngine.from_evidence_level(6) == Confidence.LOW


def test_combine_returns_weakest_confidence():
    assert (
        ConfidenceEngine.combine([Confidence.HIGH, Confidence.MEDIUM, Confidence.LOW])
        == Confidence.LOW
    )
    assert ConfidenceEngine.combine([Confidence.HIGH, Confidence.HIGH]) == Confidence.HIGH


def test_combine_empty_returns_none():
    assert ConfidenceEngine.combine([]) is None


def test_combine_evidence_levels_returns_weakest_numerically_highest():
    assert ConfidenceEngine.combine_evidence_levels([1, 3, 6]) == 6


def test_combine_evidence_levels_empty_returns_none():
    assert ConfidenceEngine.combine_evidence_levels([]) is None
