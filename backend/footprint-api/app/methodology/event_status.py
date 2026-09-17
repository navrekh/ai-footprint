from app.models.enums import EventMeasurementStatus, MetricStatus


def compute_event_status(
    energy_status: str, water_status: str, carbon_status: str
) -> EventMeasurementStatus:
    """Derives the overall completeness of a persisted event from its
    three per-metric statuses - never itself stored, always derived.

    - every metric ok               -> measured
    - some ok (or partial), not all -> partial
    - nothing measured              -> insufficient_data
    """
    statuses = {energy_status, water_status, carbon_status}
    if statuses == {MetricStatus.OK.value}:
        return EventMeasurementStatus.MEASURED
    if MetricStatus.OK.value in statuses or MetricStatus.PARTIAL.value in statuses:
        return EventMeasurementStatus.PARTIAL
    return EventMeasurementStatus.INSUFFICIENT_DATA
