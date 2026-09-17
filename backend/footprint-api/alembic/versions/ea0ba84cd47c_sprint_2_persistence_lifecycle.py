"""sprint 2 persistence lifecycle

Revision ID: ea0ba84cd47c
Revises: ea5cca7ca239
Create Date: 2026-09-17 14:02:39.472940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea0ba84cd47c'
down_revision: Union[str, None] = 'ea5cca7ca239'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- organizations: slug (backfilled from id for pre-existing rows) + status ---
    op.add_column('organizations', sa.Column('slug', sa.String(length=255), nullable=True))
    op.execute("UPDATE organizations SET slug = id WHERE slug IS NULL")
    op.alter_column('organizations', 'slug', nullable=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)
    op.add_column(
        'organizations',
        sa.Column('status', sa.String(length=16), nullable=False, server_default='active'),
    )

    # --- projects: slug (backfilled from id), description, status ---
    op.add_column('projects', sa.Column('slug', sa.String(length=255), nullable=True))
    op.execute("UPDATE projects SET slug = id WHERE slug IS NULL")
    op.alter_column('projects', 'slug', nullable=False)
    op.add_column('projects', sa.Column('description', sa.String(), nullable=True))
    op.add_column(
        'projects',
        sa.Column('status', sa.String(length=16), nullable=False, server_default='active'),
    )
    op.create_unique_constraint(
        'uq_project_organization_slug', 'projects', ['organization_id', 'slug']
    )

    # --- api_keys: organization_id (backfilled via project), expires_at, project_id nullable ---
    op.add_column('api_keys', sa.Column('organization_id', sa.String(length=64), nullable=True))
    op.execute(
        "UPDATE api_keys SET organization_id = projects.organization_id "
        "FROM projects WHERE projects.id = api_keys.project_id"
    )
    op.alter_column('api_keys', 'organization_id', nullable=False)
    op.add_column('api_keys', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    op.alter_column(
        'api_keys', 'project_id', existing_type=sa.VARCHAR(length=64), nullable=True
    )
    op.create_index(
        op.f('ix_api_keys_organization_id'), 'api_keys', ['organization_id'], unique=False
    )
    op.create_foreign_key(
        'fk_api_keys_organization_id_organizations',
        'api_keys',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE',
    )

    # --- ai_workloads: new optional fields, idempotency, filter/order indexes ---
    op.add_column(
        'ai_workloads', sa.Column('model_version', sa.String(length=64), nullable=True)
    )
    op.add_column('ai_workloads', sa.Column('input_characters', sa.Integer(), nullable=True))
    op.add_column('ai_workloads', sa.Column('output_characters', sa.Integer(), nullable=True))
    op.add_column('ai_workloads', sa.Column('duration_ms', sa.Float(), nullable=True))
    op.add_column(
        'ai_workloads', sa.Column('idempotency_key', sa.String(length=255), nullable=True)
    )
    op.create_index(
        op.f('ix_ai_workloads_activity_type'), 'ai_workloads', ['activity_type'], unique=False
    )
    op.create_index(
        op.f('ix_ai_workloads_created_at'), 'ai_workloads', ['created_at'], unique=False
    )
    op.create_index(op.f('ix_ai_workloads_model'), 'ai_workloads', ['model'], unique=False)
    op.create_index(
        'ix_ai_workloads_project_created', 'ai_workloads', ['project_id', 'created_at'],
        unique=False,
    )
    op.create_index(op.f('ix_ai_workloads_provider'), 'ai_workloads', ['provider'], unique=False)
    op.create_unique_constraint(
        'uq_workload_project_idempotency_key', 'ai_workloads', ['project_id', 'idempotency_key']
    )

    # --- estimates: denormalized provenance + created_at index ---
    op.add_column('estimates', sa.Column('provider', sa.String(length=64), nullable=True))
    op.add_column('estimates', sa.Column('model', sa.String(length=255), nullable=True))
    op.add_column('estimates', sa.Column('model_version', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_estimates_created_at'), 'estimates', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_estimates_created_at'), table_name='estimates')
    op.drop_column('estimates', 'model_version')
    op.drop_column('estimates', 'model')
    op.drop_column('estimates', 'provider')

    op.drop_constraint('uq_workload_project_idempotency_key', 'ai_workloads', type_='unique')
    op.drop_index(op.f('ix_ai_workloads_provider'), table_name='ai_workloads')
    op.drop_index('ix_ai_workloads_project_created', table_name='ai_workloads')
    op.drop_index(op.f('ix_ai_workloads_model'), table_name='ai_workloads')
    op.drop_index(op.f('ix_ai_workloads_created_at'), table_name='ai_workloads')
    op.drop_index(op.f('ix_ai_workloads_activity_type'), table_name='ai_workloads')
    op.drop_column('ai_workloads', 'idempotency_key')
    op.drop_column('ai_workloads', 'duration_ms')
    op.drop_column('ai_workloads', 'output_characters')
    op.drop_column('ai_workloads', 'input_characters')
    op.drop_column('ai_workloads', 'model_version')

    # NOTE: this will fail if any organization-level (project_id IS NULL)
    # API keys exist, since project_id cannot be restored to NOT NULL
    # while NULLs are present - an inherent, intentional limitation of
    # downgrading past the point where NULL project_id became meaningful.
    op.drop_constraint('fk_api_keys_organization_id_organizations', 'api_keys', type_='foreignkey')
    op.drop_index(op.f('ix_api_keys_organization_id'), table_name='api_keys')
    op.alter_column(
        'api_keys', 'project_id', existing_type=sa.VARCHAR(length=64), nullable=False
    )
    op.drop_column('api_keys', 'expires_at')
    op.drop_column('api_keys', 'organization_id')

    op.drop_constraint('uq_project_organization_slug', 'projects', type_='unique')
    op.drop_column('projects', 'status')
    op.drop_column('projects', 'description')
    op.drop_column('projects', 'slug')

    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_column('organizations', 'status')
    op.drop_column('organizations', 'slug')
