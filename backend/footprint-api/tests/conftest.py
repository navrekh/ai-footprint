import os
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://footprint:footprint@localhost:5432/footprint_test",
)
os.environ["ENVIRONMENT"] = "test"
os.environ["API_KEY_PREFIX"] = "afp_test"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.dependencies.db import get_db_session
from app.core.config import get_settings
from app.db.database import engine
from app.main import app

BACKEND_ROOT = os.path.dirname(os.path.dirname(__file__))


def _ensure_test_database() -> None:
    import psycopg

    settings = get_settings()
    sync_url = settings.sync_database_url.replace("postgresql+psycopg", "postgresql")
    parts = urlsplit(sync_url)
    db_name = parts.path.lstrip("/")
    admin_url = urlunsplit((parts.scheme, parts.netloc, "/postgres", "", ""))

    conn = psycopg.connect(admin_url, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        conn.close()


def _run_migrations() -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        check=True,
    )


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    _ensure_test_database()
    _run_migrations()
    yield


@pytest_asyncio.fixture
async def db_session():
    """Wraps each test in an outer transaction + SAVEPOINT so that any
    `session.commit()` calls made by application/service code only end the
    savepoint - the outer transaction (and therefore all test data) is
    always rolled back at teardown, keeping tests isolated without
    depending on TRUNCATE between runs.
    """
    async with engine.connect() as connection:
        await connection.begin()
        await connection.begin_nested()
        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()
            await connection.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def tenant(db_session):
    from tests import factories

    org = await factories.create_organization(db_session)
    project = await factories.create_project(db_session, org.id)
    api_key, raw_key = await factories.create_api_key(db_session, project.id)
    await db_session.commit()
    return {"organization": org, "project": project, "api_key": api_key, "raw_key": raw_key}


@pytest_asyncio.fixture
async def auth_headers(tenant):
    return {"Authorization": f"Bearer {tenant['raw_key']}"}


@pytest_asyncio.fixture
async def wired_model(db_session):
    """A provider + methodology + model + energy/water/carbon factors for
    provider=openai, model=test-only-model, modality=text,
    activity_type=text_generation - enough to exercise a full successful
    estimation.
    """
    from tests import factories

    provider = await factories.create_provider(db_session, "openai", modalities=["text"])
    methodology = await factories.create_methodology(db_session)
    model = await factories.create_model(db_session, provider_id=provider.id)
    await factories.create_factor(
        db_session, metric="energy", unit="Wh", value_min=0.01, value_max=0.02
    )
    await factories.create_factor(
        db_session, metric="water", unit="mL", value_min=0.02, value_max=0.03
    )
    await factories.create_factor(
        db_session, metric="carbon", unit="gCO2e", value_min=0.001, value_max=0.002
    )
    await db_session.commit()
    return {"provider": provider, "methodology": methodology, "model": model}
