"""Static, versioned benchmark definitions (docs/FRD.md section 35.3,
docs/ARCHITECTURE.md ADR-006).

A benchmark is a fixed, reproducible workload definition expressed
entirely in terms of the existing ActivityType/Modality taxonomy - it
introduces no competing taxonomy and carries no environmental
coefficients of its own. Benchmark execution resolves methodology data
through the normal estimation pipeline exactly like any other workload,
so a benchmark may legitimately return insufficient_data when no
approved factor exists for a given candidate.

This module is data, not a database table: definitions are curated,
small in number, and change by editing this file and bumping the
affected definition's `version` - the same "immutable once published,
new version on change" discipline used for methodology versions
(docs/METHODOLOGY.md section 19), applied here to workload shape rather
than environmental coefficients.
"""

from dataclasses import dataclass, field

from app.models.enums import ActivityType, Modality


@dataclass(frozen=True)
class BenchmarkDefinition:
    benchmark_id: str
    version: str
    name: str
    description: str
    activity_type: ActivityType
    modality: Modality
    # WorkloadInput-compatible fields, applied on top of a caller-supplied
    # candidate's provider/model/model_version.
    parameters: dict = field(default_factory=dict)


_DEFINITIONS: list[BenchmarkDefinition] = [
    BenchmarkDefinition(
        benchmark_id="text_generation_standard",
        version="1.0",
        name="Standard text generation",
        description="A representative conversational text-generation exchange.",
        activity_type=ActivityType.TEXT_GENERATION,
        modality=Modality.TEXT,
        parameters={"input_tokens": 500, "output_tokens": 500},
    ),
    BenchmarkDefinition(
        benchmark_id="text_reasoning_standard",
        version="1.0",
        name="Standard reasoning task",
        description="A multi-step reasoning request with a longer output than standard generation.",
        activity_type=ActivityType.TEXT_REASONING,
        modality=Modality.TEXT,
        parameters={"input_tokens": 500, "output_tokens": 2000},
    ),
    BenchmarkDefinition(
        benchmark_id="code_generation_standard",
        version="1.0",
        name="Standard code generation",
        description="Generating a small function from a natural-language description.",
        activity_type=ActivityType.CODE_GENERATION,
        modality=Modality.CODING,
        parameters={"input_tokens": 300, "output_tokens": 800},
    ),
    BenchmarkDefinition(
        benchmark_id="code_review_standard",
        version="1.0",
        name="Standard code review",
        description="Reviewing a moderate-sized diff for correctness and style.",
        activity_type=ActivityType.CODE_REVIEW,
        modality=Modality.CODING,
        parameters={"input_tokens": 1500, "output_tokens": 500},
    ),
    BenchmarkDefinition(
        benchmark_id="debugging_standard",
        version="1.0",
        name="Standard debugging session",
        description="Diagnosing a failure from an error message and surrounding code.",
        activity_type=ActivityType.DEBUGGING,
        modality=Modality.CODING,
        parameters={"input_tokens": 1200, "output_tokens": 600},
    ),
    BenchmarkDefinition(
        benchmark_id="code_refactoring_standard",
        version="1.0",
        name="Standard refactoring task",
        description="Refactoring an existing function without changing its behavior.",
        activity_type=ActivityType.CODE_REFACTORING,
        modality=Modality.CODING,
        parameters={"input_tokens": 800, "output_tokens": 800},
    ),
    BenchmarkDefinition(
        benchmark_id="image_generation_standard",
        version="1.0",
        name="Standard image generation",
        description="A single standard-resolution image generation request.",
        activity_type=ActivityType.IMAGE_GENERATION,
        modality=Modality.IMAGE,
        parameters={"image_count": 1, "image_width": 1024, "image_height": 1024},
    ),
    BenchmarkDefinition(
        benchmark_id="video_generation_standard",
        version="1.0",
        name="Standard short video generation",
        description="A short standard-resolution generated video clip.",
        activity_type=ActivityType.VIDEO_GENERATION,
        modality=Modality.VIDEO,
        parameters={"video_seconds": 5, "video_resolution": "1080p"},
    ),
    BenchmarkDefinition(
        benchmark_id="audio_generation_standard",
        version="1.0",
        name="Standard audio generation",
        description="A short generated audio clip.",
        activity_type=ActivityType.AUDIO_GENERATION,
        modality=Modality.AUDIO,
        parameters={"audio_seconds": 30},
    ),
    BenchmarkDefinition(
        benchmark_id="speech_to_text_standard",
        version="1.0",
        name="Standard speech-to-text transcription",
        description="Transcribing a short audio clip to text.",
        activity_type=ActivityType.SPEECH_TO_TEXT,
        modality=Modality.AUDIO,
        parameters={"audio_seconds": 60},
    ),
    BenchmarkDefinition(
        benchmark_id="vision_standard",
        version="1.0",
        name="Standard vision analysis",
        description="Analyzing a single standard-resolution image.",
        activity_type=ActivityType.VISION,
        modality=Modality.IMAGE,
        parameters={"image_count": 1, "image_width": 1024, "image_height": 1024},
    ),
    BenchmarkDefinition(
        benchmark_id="embedding_standard",
        version="1.0",
        name="Standard text embedding",
        description="Generating an embedding vector for a moderate-length text passage.",
        activity_type=ActivityType.EMBEDDING,
        modality=Modality.TEXT,
        parameters={"input_tokens": 500, "output_tokens": 0},
    ),
    BenchmarkDefinition(
        benchmark_id="rag_standard",
        version="1.0",
        name="Standard retrieval-augmented generation",
        description="A RAG request combining retrieved context with a generated answer.",
        activity_type=ActivityType.RAG,
        modality=Modality.TEXT,
        parameters={"input_tokens": 2000, "output_tokens": 500},
    ),
    BenchmarkDefinition(
        benchmark_id="coding_agent_standard",
        version="1.0",
        name="Standard coding agent step",
        description="A single tool-augmented inference step within a coding agent session.",
        activity_type=ActivityType.CODING_AGENT,
        modality=Modality.CODING,
        parameters={"input_tokens": 1000, "output_tokens": 500, "tool_calls": 2},
    ),
    BenchmarkDefinition(
        benchmark_id="agent_workflow_standard",
        version="1.0",
        name="Standard agent workflow step",
        description="A single step within a general multi-step autonomous agent workflow.",
        activity_type=ActivityType.AGENT_WORKFLOW,
        modality=Modality.AGENT,
        parameters={"input_tokens": 800, "output_tokens": 400, "tool_calls": 1},
    ),
]

# Deterministic ordering, independent of definition order above or any
# database/insertion order (there is no database - this is belt and
# braces for anyone iterating _DEFINITIONS directly in the future).
_BENCHMARKS_BY_ID: dict[str, BenchmarkDefinition] = {
    definition.benchmark_id: definition
    for definition in sorted(_DEFINITIONS, key=lambda d: d.benchmark_id)
}


def list_benchmarks(
    *, activity_type: ActivityType | None = None, modality: Modality | None = None
) -> list[BenchmarkDefinition]:
    results = list(_BENCHMARKS_BY_ID.values())
    if activity_type is not None:
        results = [d for d in results if d.activity_type == activity_type]
    if modality is not None:
        results = [d for d in results if d.modality == modality]
    return results


def get_benchmark(benchmark_id: str) -> BenchmarkDefinition | None:
    return _BENCHMARKS_BY_ID.get(benchmark_id)
