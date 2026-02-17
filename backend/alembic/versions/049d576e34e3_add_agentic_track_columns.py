"""add agentic track columns

Revision ID: 049d576e34e3
Revises:
Create Date: 2026-02-16 15:40:36.821293

Adds columns for dual-track evaluation support (standard STAR + agentic):
- answers: track, interview_type (with server defaults for existing rows)
- evaluations: evaluation_type, agentic_scores, agentic_result, hiring_decision
- questions: track, interview_type, scenario_id, tags, ideal_answer_points
- answers.target_company_id: made nullable (agentic track doesn't require company)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '049d576e34e3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add agentic track support columns."""

    # --- answers table ---
    # server_default populates existing rows, then we keep it as the model default
    op.add_column('answers', sa.Column(
        'track', sa.String(length=20), nullable=False, server_default='standard'
    ))
    op.add_column('answers', sa.Column(
        'interview_type', sa.String(length=20), nullable=False, server_default='behavioral'
    ))
    # Make target_company_id nullable (agentic evaluations don't require a company)
    op.alter_column('answers', 'target_company_id',
                    existing_type=sa.UUID(),
                    nullable=True)

    # --- evaluations table ---
    op.add_column('evaluations', sa.Column(
        'evaluation_type', sa.String(length=20), nullable=False, server_default='standard'
    ))
    op.add_column('evaluations', sa.Column(
        'agentic_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True
    ))
    op.add_column('evaluations', sa.Column(
        'agentic_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True
    ))
    op.add_column('evaluations', sa.Column(
        'hiring_decision', sa.String(length=20), nullable=True
    ))

    # --- questions table ---
    op.add_column('questions', sa.Column(
        'track', sa.String(length=20), nullable=False, server_default='standard'
    ))
    op.add_column('questions', sa.Column(
        'interview_type', sa.String(length=20), nullable=False, server_default='behavioral'
    ))
    op.add_column('questions', sa.Column(
        'scenario_id', sa.String(length=50), nullable=True
    ))
    op.add_column('questions', sa.Column(
        'tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True
    ))
    op.add_column('questions', sa.Column(
        'ideal_answer_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True
    ))


def downgrade() -> None:
    """Remove agentic track columns."""
    # --- questions ---
    op.drop_column('questions', 'ideal_answer_points')
    op.drop_column('questions', 'tags')
    op.drop_column('questions', 'scenario_id')
    op.drop_column('questions', 'interview_type')
    op.drop_column('questions', 'track')

    # --- evaluations ---
    op.drop_column('evaluations', 'hiring_decision')
    op.drop_column('evaluations', 'agentic_result')
    op.drop_column('evaluations', 'agentic_scores')
    op.drop_column('evaluations', 'evaluation_type')

    # --- answers ---
    op.alter_column('answers', 'target_company_id',
                    existing_type=sa.UUID(),
                    nullable=False)
    op.drop_column('answers', 'interview_type')
    op.drop_column('answers', 'track')
