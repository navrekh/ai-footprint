import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models.estimate import Estimate
from app.models.workload import AIWorkload
from app.schemas.workload import EventCreateRequest
from app.services.workload_service import WorkloadService
from tests import factories


def _fake_integrity_error(message: str) -> IntegrityError:
    return IntegrityError("INSERT ...", {}, Exception(message))


def test_is_idempotency_key_conflict_detects_the_right_constraint():
    exc = _fake_integrity_error(
        'duplicate key value violates unique constraint '
        '"uq_workload_project_idempotency_key"'
    )

    assert WorkloadService._is_idempotency_key_conflict(exc) is True


def test_is_idempotency_key_conflict_ignores_unrelated_constraints():
    exc = _fake_integrity_error(
        'insert or update on table "ai_workloads" violates foreign key '
        'constraint "ai_workloads_project_id_fkey"'
    )

    assert WorkloadService._is_idempotency_key_conflict(exc) is False


@pytest.mark.asyncio
async def test_concurrent_insert_with_same_idempotency_key_returns_winning_record(
    db_session, wired_model
):
    """Reproduces the real unique-constraint conflict path (sprint 2
    follow-up review, item 2): a competing transaction commits a
    workload under the same (project_id, idempotency_key) after this
    request's own pre-check has already run - so the pre-check finds
    nothing, but the actual INSERT hits the live database constraint.
    The pre-check timing is simulated (single test session, no real
    second connection); the constraint violation itself is real, not
    mocked.
    """
    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    await db_session.commit()

    idempotency_key = "race-condition-key"
    payload = EventCreateRequest(
        provider="openai",
        model="test-only-model",
        modality="text",
        activity_type="text_generation",
        input_tokens=10,
        output_tokens=10,
        idempotency_key=idempotency_key,
    )

    service = WorkloadService(db_session)

    original_find = service._find_existing_by_idempotency_key
    call_count = 0

    async def find_with_simulated_race_on_first_call(project_id: str, key: str):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Simulate the race window: another request is about to win,
            # but has not committed yet as far as this request can see.
            return None
        return await original_find(project_id, key)

    service._find_existing_by_idempotency_key = find_with_simulated_race_on_first_call

    # The "concurrent" request that wins the race, committed directly.
    winning_workload, winning_estimate, was_replay = await WorkloadService(
        db_session
    ).create_event(organization_id=org.id, project_id=project.id, payload=payload)
    assert was_replay is False

    # Our request runs after the winner already committed. Its own
    # pre-check (mocked above) reports nothing found, so it proceeds to
    # insert - and must hit the real unique constraint, then recover.
    workload, estimate, is_replay = await service.create_event(
        organization_id=org.id, project_id=project.id, payload=payload
    )

    assert is_replay is True
    assert workload.id == winning_workload.id
    assert estimate.id == winning_estimate.id

    workload_count = (
        await db_session.execute(
            select(func.count())
            .select_from(AIWorkload)
            .where(AIWorkload.idempotency_key == idempotency_key)
        )
    ).scalar_one()
    assert workload_count == 1

    estimate_count = (
        await db_session.execute(
            select(func.count()).select_from(Estimate).where(Estimate.workload_id == workload.id)
        )
    ).scalar_one()
    assert estimate_count == 1


@pytest.mark.asyncio
async def test_unrelated_integrity_error_is_not_treated_as_idempotent_replay(
    db_session, wired_model
):
    """A workload referencing a project that has since been deleted (a
    real foreign-key violation, unrelated to idempotency) must propagate
    as an error, never be silently treated as a successful replay.
    """
    org = await factories.create_organization(db_session)
    await db_session.commit()

    payload = EventCreateRequest(
        provider="openai",
        model="test-only-model",
        modality="text",
        activity_type="text_generation",
        input_tokens=10,
        output_tokens=10,
        idempotency_key="unrelated-error-key",
    )

    service = WorkloadService(db_session)

    async def find_returns_none(project_id: str, key: str):
        return None

    service._find_existing_by_idempotency_key = find_returns_none

    bogus_project_id = "proj_does_not_exist_at_all"

    with pytest.raises(IntegrityError):
        await service.create_event(
            organization_id=org.id, project_id=bogus_project_id, payload=payload
        )
