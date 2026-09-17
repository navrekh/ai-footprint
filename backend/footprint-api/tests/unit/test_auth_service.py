from datetime import UTC, datetime, timedelta

import pytest

from app.core.errors import ApiKeyExpiredError, InvalidApiKeyError
from app.models.enums import ApiKeyStatus
from app.services.auth_service import AuthService
from tests import factories


@pytest.mark.asyncio
async def test_authenticate_project_scoped_key_resolves_project_and_organization(db_session):
    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    _, raw_key = await factories.create_api_key(db_session, project.id)
    await db_session.commit()

    context = await AuthService(db_session).authenticate(raw_key)

    assert context.organization.id == org.id
    assert context.project is not None
    assert context.project.id == project.id


@pytest.mark.asyncio
async def test_authenticate_organization_level_key_has_no_project(db_session):
    org = await factories.create_organization(db_session)
    _, raw_key = await factories.create_api_key(db_session, organization_id=org.id)
    await db_session.commit()

    context = await AuthService(db_session).authenticate(raw_key)

    assert context.organization.id == org.id
    assert context.project is None


@pytest.mark.asyncio
async def test_authenticate_wrong_key_raises(db_session):
    with pytest.raises(InvalidApiKeyError):
        await AuthService(db_session).authenticate("afp_test_not-a-real-key")


@pytest.mark.asyncio
async def test_authenticate_revoked_key_raises(db_session):
    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    api_key, raw_key = await factories.create_api_key(db_session, project.id)
    api_key.status = ApiKeyStatus.REVOKED.value
    await db_session.commit()

    with pytest.raises(InvalidApiKeyError):
        await AuthService(db_session).authenticate(raw_key)


@pytest.mark.asyncio
async def test_authenticate_expired_key_raises_distinct_error(db_session):
    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    _, raw_key = await factories.create_api_key(
        db_session, project.id, expires_at=datetime.now(UTC) - timedelta(days=1)
    )
    await db_session.commit()

    with pytest.raises(ApiKeyExpiredError):
        await AuthService(db_session).authenticate(raw_key)


@pytest.mark.asyncio
async def test_authenticate_not_yet_expired_key_succeeds(db_session):
    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    _, raw_key = await factories.create_api_key(
        db_session, project.id, expires_at=datetime.now(UTC) + timedelta(days=1)
    )
    await db_session.commit()

    context = await AuthService(db_session).authenticate(raw_key)

    assert context.organization.id == org.id


@pytest.mark.asyncio
async def test_authenticate_updates_last_used_at(db_session):
    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    api_key, raw_key = await factories.create_api_key(db_session, project.id)
    await db_session.commit()
    assert api_key.last_used_at is None

    await AuthService(db_session).authenticate(raw_key)

    await db_session.refresh(api_key)
    assert api_key.last_used_at is not None
