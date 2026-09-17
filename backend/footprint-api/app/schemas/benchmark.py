from pydantic import BaseModel, Field

from app.models.enums import ActivityType, Modality
from app.schemas.common import ComparisonCandidate
from app.schemas.compare import ComparisonResultItem


class BenchmarkDefinitionRead(BaseModel):
    benchmark_id: str
    version: str
    name: str
    description: str
    activity_type: ActivityType
    modality: Modality
    parameters: dict


class BenchmarkListResponse(BaseModel):
    items: list[BenchmarkDefinitionRead]
    total: int


class BenchmarkRunRequest(BaseModel):
    benchmark_id: str
    candidates: list[ComparisonCandidate] = Field(min_length=2)


class BenchmarkRunResponse(BaseModel):
    benchmark_id: str
    benchmark_version: str
    modality: Modality
    activity_type: ActivityType
    results: list[ComparisonResultItem]
