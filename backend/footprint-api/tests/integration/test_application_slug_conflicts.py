import pytest

from app.models.application import Application


@pytest.mark.asyncio
async def test_application_slug_conflict_retries_with_suffix(
    client, auth_headers, tenant, db_session
):
    """Reproduces the real unique-index violation (not mocked), the same
    class of race already hardened for organizations/projects in Sprint 2:
    an application already occupies the slug that slugify("Widgets")
    would produce within this project, so the first insert attempt
    inside allocate_unique_slug must fail and retry with a suffixed
    candidate rather than 500ing.
    """
    existing = Application(
        project_id=tenant["project"].id, name="Widgets (existing)", slug="widgets"
    )
    db_session.add(existing)
    await db_session.commit()

    response = await client.post(
        "/v1/applications", json={"name": "Widgets"}, headers=auth_headers
    )

    assert response.status_code == 200
    new_slug = response.json()["slug"]
    assert new_slug != "widgets"
    assert new_slug.startswith("widgets-")


@pytest.mark.asyncio
async def test_same_slug_allowed_in_different_projects(client, auth_headers, tenant, db_session):
    from tests import factories

    other_project = await factories.create_project(db_session, tenant["organization"].id)
    await factories.create_application(db_session, other_project.id, name="Shared Name")
    await db_session.commit()

    # Same name, different (this tenant's own) project - must not collide,
    # since application slugs are scoped per-project, not globally.
    response = await client.post(
        "/v1/applications", json={"name": "Shared Name"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["slug"] == "shared-name"


@pytest.mark.asyncio
async def test_duplicate_max_length_application_name_does_not_overflow_slug_column(
    client, auth_headers
):
    long_name = "z" * 255

    first = await client.post(
        "/v1/applications", json={"name": long_name}, headers=auth_headers
    )
    second = await client.post(
        "/v1/applications", json={"name": long_name}, headers=auth_headers
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(first.json()["slug"]) <= 255
    assert len(second.json()["slug"]) <= 255
    assert first.json()["slug"] != second.json()["slug"]
