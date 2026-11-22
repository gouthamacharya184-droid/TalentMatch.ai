"""initial_schema_with_indexes

Revision ID: a6598588ee68
Revises: 
Create Date: 2026-11-22 22:51:26.084928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6598588ee68'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_jobs_campaign_id_campaigns', 'campaigns', ['campaign_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('matching_analyses', schema=None) as batch_op:
        batch_op.alter_column('projects_score',
               existing_type=sa.FLOAT(),
               nullable=False,
               existing_server_default=sa.text('(0.0)'))
        batch_op.alter_column('preferred_score',
               existing_type=sa.FLOAT(),
               nullable=False,
               existing_server_default=sa.text('(0.0)'))
        batch_op.create_index(batch_op.f('ix_matching_analyses_evaluation_run_id'), ['evaluation_run_id'], unique=False)
        batch_op.create_foreign_key('fk_matching_analyses_evaluation_run_id', 'evaluation_runs', ['evaluation_run_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('resumes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_resumes_content_hash'), ['content_hash'], unique=False)

    with op.batch_alter_table('revoked_tokens', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_revoked_tokens_expires_at'), ['expires_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('revoked_tokens', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_revoked_tokens_expires_at'))

    with op.batch_alter_table('resumes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_resumes_content_hash'))

    with op.batch_alter_table('matching_analyses', schema=None) as batch_op:
        batch_op.drop_constraint('fk_matching_analyses_evaluation_run_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_matching_analyses_evaluation_run_id'))
        batch_op.alter_column('preferred_score',
               existing_type=sa.FLOAT(),
               nullable=True,
               existing_server_default=sa.text('(0.0)'))
        batch_op.alter_column('projects_score',
               existing_type=sa.FLOAT(),
               nullable=True,
               existing_server_default=sa.text('(0.0)'))

    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.drop_constraint('fk_jobs_campaign_id_campaigns', type_='foreignkey')
