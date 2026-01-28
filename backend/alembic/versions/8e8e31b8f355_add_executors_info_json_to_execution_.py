"""add executors_info_json to execution_data

Revision ID: 8e8e31b8f355
Revises: b1c3f4a5d6e7
Create Date: 2026-01-28 21:11:15.876104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8e8e31b8f355'
down_revision: Union[str, None] = 'b1c3f4a5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add executors_info_json column to execution_data table
    op.add_column('execution_data', sa.Column('executors_info_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove executors_info_json column from execution_data table
    op.drop_column('execution_data', 'executors_info_json')
