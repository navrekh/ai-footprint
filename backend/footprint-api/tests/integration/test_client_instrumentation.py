"""Sprint 6 - event ingestion, persistence, estimation invariance, and
authorization tests for the client/integration metadata contract
(FRD section 38). Client metadata is observational only: these tests
prove it is persisted and returned where relevant, but never changes
which organization/project/application a workload belongs to, never
changes idempotent-replay behavior, and never changes the resulting
estimate.
"""

import pytest
from sqlalchemy import select

from app.models.workload import AIWorkload
from tests import factories

WORKLOAD = {
    "provider": "openai",
    "model": "test-only-model",
    "modality": "text",
    "activity_type": "text_generation",
    "input_tokens": 100,
    "output_tokens": 50,
}

CLIENT_A = {
    "client_type": "python_sdk",
    "client_name": "aifootprint-python",
    "client_version": "0.5.0",
    "integration_type": "backend_middleware",
    "integration_version": "1.2.0",
    "runtime": "python/3.13",
}

CLIENT_B = {
    "client_type": "browser_extension",
    "client_name": "aifootprint-extension",
    "client_version": "9.9.9",
}


@pytest.mark.asyncio
async def test_event_persists_and_returns_client_metadata(
    client, auth_headers, wired_model
):
    response = await client.post(
        "/v1/events", json={**WORKLOAD, "client": CLIENT_A}, headers=auth_headers
    )

    assert response.status_code == 200
    workload_id = response.json()["workload_id"]

    read = await client.get(f"/v1/workloads/{workload_id}", headers=auth_headers)
    assert read.status_code == 200
    assert read.json()["client"] == CLIENT_A


@pytest.mark.asyncio
async def test_event_without_client_metadata_remains_backward_compatible(
    client, auth_headers, wired_model
):
    response = await client.post("/v1/events", json=WORKLOAD, headers=auth_headers)

    assert response.status_code == 200
    workload_id = response.json()["workload_id"]

    read = await client.get(f"/v1/workloads/{workload_id}", headers=auth_headers)
    assert read.json()["client"] is None


@pytest.mark.asyncio
async def test_idempotent_replay_returns_original_client_metadata_unchanged(
    client, auth_headers, wired_model
):
    """A retried request with the *same* idempotency_key but *different*
    client metadata (e.g. a retry issued by a different client surface)
    must still be treated as a replay of the original measurement -
    the originally persisted client metadata must not be overwritten.
    """
    first_payload = {**WORKLOAD, "idempotency_key": "retry-1", "client": CLIENT_A}
    second_payload = {**WORKLOAD, "idempotency_key": "retry-1", "client": CLIENT_B}

    first = await client.post("/v1/events", json=first_payload, headers=auth_headers)
    second = await client.post("/v1/events", json=second_payload, headers=auth_headers)

    assert first.json()["idempotent_replay"] is False
    assert second.json()["idempotent_replay"] is True
    assert first.json()["workload_id"] == second.json()["workload_id"]

    read = await client.get(f"/v1/workloads/{first.json()['workload_id']}", headers=auth_headers)
    assert read.json()["client"] == CLIENT_A


@pytest.mark.asyncio
async def test_client_metadata_cannot_redirect_workload_ownership(
    client, auth_headers, tenant, db_session, wired_model
):
    """Client metadata carries no organization/project/application
    fields at all, so stuffing authorization-shaped keys into it must
    have zero effect: the workload is still owned by the authenticated
    key's own organization/project, and unknown keys are silently
    dropped rather than interpreted.
    """
    other_org = await factories.create_organization(db_session, name="Other Org")
    other_project = await factories.create_project(db_session, other_org.id)
    await db_session.commit()

    payload = {
        **WORKLOAD,
        "client": {
            **CLIENT_A,
            "organization_id": other_org.id,
            "project_id": other_project.id,
        },
    }
    response = await client.post("/v1/events", json=payload, headers=auth_headers)

    assert response.status_code == 200
    workload_id = response.json()["workload_id"]

    workload = (
        await db_session.execute(select(AIWorkload).where(AIWorkload.id == workload_id))
    ).scalar_one()
    assert workload.organization_id == tenant["organization"].id
    assert workload.project_id == tenant["project"].id
    assert workload.organization_id != other_org.id
    assert workload.project_id != other_project.id


@pytest.mark.asyncio
async def test_project_scoped_key_isolation_is_unaffected_by_client_metadata(
    client, auth_headers, db_session, tenant, wired_model
):
    """The existing project-isolation check (Sprint 2/3) must reject a
    cross-project `project_id` exactly as before, regardless of any
    client metadata supplied alongside it.
    """
    other_project = await factories.create_project(db_session, tenant["organization"].id)
    await db_session.commit()

    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "project_id": other_project.id, "client": CLIENT_A},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_invalid_client_type_is_rejected_with_422(client, auth_headers, wired_model):
    response = await client.post(
        "/v1/events",
        json={**WORKLOAD, "client": {"client_type": "not_a_real_type"}},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_estimate_is_identical_regardless_of_client_metadata(
    client, auth_headers, wired_model
):
    """Estimation invariance (FRD section 38 / critical test): the same
    workload quantities/provider/model/modality/activity_type must
    produce byte-identical energy/water/carbon ranges, confidence,
    evidence_level, methodology_version and assumptions whether client
    metadata is omitted, CLIENT_A, or CLIENT_B.
    """

    def strip_volatile(body: dict) -> dict:
        return {k: v for k, v in body.items() if k not in ("estimate_id", "created_at")}

    baseline = await client.post("/v1/estimate", json=WORKLOAD, headers=auth_headers)
    with_client_a = await client.post(
        "/v1/estimate", json={**WORKLOAD, "client": CLIENT_A}, headers=auth_headers
    )
    with_client_b = await client.post(
        "/v1/estimate", json={**WORKLOAD, "client": CLIENT_B}, headers=auth_headers
    )

    assert baseline.status_code == with_client_a.status_code == with_client_b.status_code == 200
    baseline_body = strip_volatile(baseline.json())
    assert strip_volatile(with_client_a.json()) == baseline_body
    assert strip_volatile(with_client_b.json()) == baseline_body


@pytest.mark.asyncio
async def test_persisted_estimate_is_identical_regardless_of_client_metadata(
    client, auth_headers, wired_model, db_session
):
    """Same as above, but through the persisted /v1/events path - proves
    the estimation invariance holds end to end, not only for the
    stateless endpoint.
    """
    from app.models.estimate import Estimate

    def snapshot(estimate: Estimate) -> dict:
        return {
            "energy_status": estimate.energy_status,
            "energy_min_wh": estimate.energy_min_wh,
            "energy_max_wh": estimate.energy_max_wh,
            "water_status": estimate.water_status,
            "water_min_ml": estimate.water_min_ml,
            "water_max_ml": estimate.water_max_ml,
            "carbon_status": estimate.carbon_status,
            "carbon_min_g": estimate.carbon_min_g,
            "carbon_max_g": estimate.carbon_max_g,
            "confidence": estimate.confidence,
            "evidence_level": estimate.evidence_level,
            "accounting_boundary": estimate.accounting_boundary,
            "methodology_version": estimate.methodology_version,
            "assumptions": estimate.assumptions,
        }

    async def create_and_snapshot(client_block: dict | None) -> dict:
        payload = {**WORKLOAD, "client": client_block} if client_block else dict(WORKLOAD)
        response = await client.post("/v1/events", json=payload, headers=auth_headers)
        estimate_id = response.json()["estimate_id"]
        estimate = (
            await db_session.execute(select(Estimate).where(Estimate.id == estimate_id))
        ).scalar_one()
        return snapshot(estimate)

    baseline = await create_and_snapshot(None)
    variant_a = await create_and_snapshot(CLIENT_A)
    variant_b = await create_and_snapshot(CLIENT_B)

    assert variant_a == baseline
    assert variant_b == baseline


@pytest.mark.asyncio
async def test_batch_estimate_accepts_client_metadata_per_item(
    client, auth_headers, wired_model
):
    response = await client.post(
        "/v1/batch-estimate",
        json={"workloads": [{**WORKLOAD, "client": CLIENT_A}, {**WORKLOAD, "client": CLIENT_B}]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["successful_estimates"] == 2
    assert body["results"][0]["status"] == "success"
    assert body["results"][1]["status"] == "success"
