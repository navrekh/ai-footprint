import pytest
from sqlalchemy import inspect

from app.db.database import engine
from app.models import Base

EXPECTED_TABLES = {
    "organizations",
    "projects",
    "api_keys",
    "providers",
    "models",
    "methodologies",
    "methodology_factors",
    "ai_workloads",
    "estimates",
}


@pytest.mark.asyncio
async def test_alembic_migrations_created_all_expected_tables():
    async with engine.connect() as connection:
        table_names = await connection.run_sync(
            lambda sync_conn: set(inspect(sync_conn).get_table_names())
        )

    assert EXPECTED_TABLES.issubset(table_names)
    assert EXPECTED_TABLES.issubset(set(Base.metadata.tables.keys()))
