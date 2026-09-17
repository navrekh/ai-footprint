import pytest

from app.models.organization import Organization
from app.models.project import Project


@pytest.mark.asyncio
async def test_organization_slug_conflict_retries_with_suffix(client, db_session):
    """Reproduces the real unique-index violation (not mocked): an
    organization already occupies the slug that slugify("Acme") would
    produce, so the first insert attempt inside allocate_unique_slug
    must fail and retry with a suffixed candidate rather than 500ing.
    """
    existing = Organization(name="Acme (existing)", slug="acme")
    db_session.add(existing)
    await db_session.commit()

    response = await client.post("/v1/organizations", json={"name": "Acme"})

    assert response.status_code == 200
    new_slug = response.json()["organization"]["slug"]
    assert new_slug != "acme"
    assert new_slug.startswith("acme-")


@pytest.mark.asyncio
async def test_project_slug_conflict_retries_with_suffix(
    client, auth_headers, tenant, db_session
):
    existing = Project(
        organization_id=tenant["organization"].id, name="Widgets (existing)", slug="widgets"
    )
    db_session.add(existing)
    await db_session.commit()

    response = await client.post(
        "/v1/projects", json={"name": "Widgets"}, headers=auth_headers
    )

    assert response.status_code == 200
    new_slug = response.json()["slug"]
    assert new_slug != "widgets"
    assert new_slug.startswith("widgets-")


@pytest.mark.asyncio
async def test_duplicate_max_length_organization_name_does_not_overflow_slug_column(
    client,
):
    """End-to-end reproduction of the exact overflow scenario: a
    255-character name submitted twice must not 500 on the second
    request, and the resulting slug must still fit the column.
    """
    long_name = "x" * 255

    first = await client.post("/v1/organizations", json={"name": long_name})
    second = await client.post("/v1/organizations", json={"name": long_name})

    assert first.status_code == 200
    assert second.status_code == 200
    first_slug = first.json()["organization"]["slug"]
    second_slug = second.json()["organization"]["slug"]
    assert len(first_slug) <= 255
    assert len(second_slug) <= 255
    assert first_slug != second_slug


@pytest.mark.asyncio
async def test_duplicate_max_length_project_name_does_not_overflow_slug_column(
    client, auth_headers
):
    long_name = "y" * 255

    first = await client.post("/v1/projects", json={"name": long_name}, headers=auth_headers)
    second = await client.post("/v1/projects", json={"name": long_name}, headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(first.json()["slug"]) <= 255
    assert len(second.json()["slug"]) <= 255
    assert first.json()["slug"] != second.json()["slug"]
