from app.core.errors import InvalidWorkloadError
from app.models.enums import Modality
from app.schemas.workload import WorkloadInput


class WorkloadValidator:
    """Pipeline stage 1: business-rule validation beyond Pydantic's field
    constraints (which already enforce non-negative quantities and
    activity/modality compatibility - see WorkloadInput).
    """

    def validate(self, workload: WorkloadInput) -> None:
        if workload.modality == Modality.IMAGE and workload.image_count is not None:
            if workload.image_count < 1:
                raise InvalidWorkloadError("image_count must be at least 1 when provided.")

        if workload.modality == Modality.VIDEO and workload.video_seconds is not None:
            if workload.video_seconds <= 0:
                raise InvalidWorkloadError("video_seconds must be greater than 0 when provided.")

        if workload.modality == Modality.AUDIO and workload.audio_seconds is not None:
            if workload.audio_seconds <= 0:
                raise InvalidWorkloadError("audio_seconds must be greater than 0 when provided.")

        if (
            workload.modality == Modality.TEXT
            and workload.input_tokens is not None
            and workload.output_tokens is not None
            and workload.input_tokens == 0
            and workload.output_tokens == 0
        ):
            raise InvalidWorkloadError(
                "text workloads with input_tokens and output_tokens both set to 0 "
                "carry no measurable quantity."
            )
