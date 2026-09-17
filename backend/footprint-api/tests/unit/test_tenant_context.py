import pytest

from app.core.errors import ForbiddenError, MissingParameterError, NotFoundError
from app.services.auth_service import AuthContext
from app.services.tenant_context import resolve_optional_project_filter, resolve_target_project_id
from tests import factories


@pytest.mark.asyncio
async def test_project_scoped_key_resolves_to_its_own_project(db_session):
    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    api_key, _ = await factories.create_api_key(db_session, project.id)
    await db_session.commit()
    auth = AuthContext(api_key=api_key, organization=org, project=project)

    resolved = await resolve_target_project_id(db_session, auth, None)

    assert resolved == project.id


@pytest.mark.asyncio
async def test_project_scoped_key_rejects_mismatched_explicit_project_id(db_session):
    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    other_project = await factories.create_project(db_session, org.id)
    api_key, _ = await factories.create_api_key(db_session, project.id)
    await db_session.commit()
    auth = AuthContext(api_key=api_key, organization=org, project=project)

    with pytest.raises(ForbiddenError):
        await resolve_target_project_id(db_session, auth, other_project.id)


@pytest.mark.asyncio
async def test_org_level_key_requires_explicit_project_id(db_session):
    org = await factories.create_organization(db_session)
    api_key, _ = await factories.create_api_key(db_session, organization_id=org.id)
    await db_session.commit()
    auth = AuthContext(api_key=api_key, organization=org, project=None)

    with pytest.raises(MissingParameterError):
        await resolve_target_project_id(db_session, auth, None)


@pytest.mark.asyncio
async def test_org_level_key_resolves_explicit_project_id(db_session):
    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    api_key, _ = await factories.create_api_key(db_session, organization_id=org.id)
    await db_session.commit()
    auth = AuthContext(api_key=api_key, organization=org, project=None)

    resolved = await resolve_target_project_id(db_session, auth, project.id)

    assert resolved == project.id


@pytest.mark.asyncio
async def test_org_level_key_cannot_target_another_organizations_project(db_session):
    org_a = await factories.create_organization(db_session, name="Org A")
    org_b = await factories.create_organization(db_session, name="Org B")
    project_b = await factories.create_project(db_session, org_b.id)
    api_key, _ = await factories.create_api_key(db_session, organization_id=org_a.id)
    await db_session.commit()
    auth = AuthContext(api_key=api_key, organization=org_a, project=None)

    with pytest.raises(NotFoundError):
        await resolve_target_project_id(db_session, auth, project_b.id)


def test_resolve_optional_project_filter_hard_scopes_project_key():
    auth = AuthContext(api_key=None, organization=None, project=type("P", (), {"id": "proj_1"}))

    assert resolve_optional_project_filter(auth, "proj_other") == "proj_1"


def test_resolve_optional_project_filter_passes_through_for_org_level_key():
    auth = AuthContext(api_key=None, organization=None, project=None)

    assert resolve_optional_project_filter(auth, "proj_x") == "proj_x"
    assert resolve_optional_project_filter(auth, None) is None
