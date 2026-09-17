from app.models.enums import CONFIDENCE_ORDER, Confidence

_EVIDENCE_LEVEL_CONFIDENCE: dict[int, Confidence] = {
    1: Confidence.HIGH,
    2: Confidence.HIGH,
    3: Confidence.MEDIUM,
    4: Confidence.MEDIUM,
    5: Confidence.LOW,
    6: Confidence.LOW,
}


class ConfidenceEngine:
    """Derives and combines confidence labels per METHODOLOGY.md section 14.

    Confidence is not a statistical probability - it is a qualitative
    label describing evidence strength. When an estimate draws on more
    than one factor (e.g. energy + water from different sources), the
    combined confidence is never stronger than its weakest contributor.
    """

    @staticmethod
    def from_evidence_level(evidence_level: int) -> Confidence:
        return _EVIDENCE_LEVEL_CONFIDENCE.get(evidence_level, Confidence.LOW)

    @staticmethod
    def combine(confidences: list[Confidence]) -> Confidence | None:
        if not confidences:
            return None
        return min(confidences, key=lambda c: CONFIDENCE_ORDER[c])

    @staticmethod
    def combine_evidence_levels(levels: list[int]) -> int | None:
        if not levels:
            return None
        return max(levels)
