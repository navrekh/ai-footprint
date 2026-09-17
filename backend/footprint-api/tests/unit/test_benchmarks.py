from app.methodology.benchmarks import get_benchmark, list_benchmarks
from app.models.enums import ActivityType, Modality


def test_listing_is_deterministic_across_calls():
    first = [d.benchmark_id for d in list_benchmarks()]
    second = [d.benchmark_id for d in list_benchmarks()]

    assert first == second
    assert len(first) > 0


def test_listing_is_sorted_by_benchmark_id():
    ids = [d.benchmark_id for d in list_benchmarks()]

    assert ids == sorted(ids)


def test_every_definition_has_a_version():
    for definition in list_benchmarks():
        assert definition.version


def test_every_definition_uses_the_existing_taxonomy():
    for definition in list_benchmarks():
        assert isinstance(definition.activity_type, ActivityType)
        assert isinstance(definition.modality, Modality)


def test_filter_by_activity_type():
    results = list_benchmarks(activity_type=ActivityType.CODE_REVIEW)

    assert len(results) >= 1
    assert all(d.activity_type == ActivityType.CODE_REVIEW for d in results)


def test_filter_by_modality():
    results = list_benchmarks(modality=Modality.IMAGE)

    assert len(results) >= 1
    assert all(d.modality == Modality.IMAGE for d in results)


def test_filter_by_activity_type_and_modality_combined():
    results = list_benchmarks(activity_type=ActivityType.TEXT_GENERATION, modality=Modality.TEXT)

    assert len(results) == 1
    assert results[0].benchmark_id == "text_generation_standard"


def test_filter_with_no_matches_returns_empty_list():
    results = list_benchmarks(activity_type=ActivityType.VIDEO_GENERATION, modality=Modality.TEXT)

    assert results == []


def test_get_benchmark_returns_known_definition():
    definition = get_benchmark("text_generation_standard")

    assert definition is not None
    assert definition.benchmark_id == "text_generation_standard"
    assert definition.activity_type == ActivityType.TEXT_GENERATION
    assert definition.modality == Modality.TEXT
    assert definition.parameters["input_tokens"] == 500


def test_get_benchmark_returns_none_for_unknown_id():
    assert get_benchmark("does_not_exist") is None
