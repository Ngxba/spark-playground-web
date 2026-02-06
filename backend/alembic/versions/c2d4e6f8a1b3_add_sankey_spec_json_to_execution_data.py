"""add sankey_spec_json to execution_data

Revision ID: c2d4e6f8a1b3
Revises: 8e8e31b8f355
Create Date: 2026-02-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c2d4e6f8a1b3'
down_revision: Union[str, None] = '8e8e31b8f355'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('execution_data', sa.Column('sankey_spec_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('execution_data', 'sankey_spec_json')
