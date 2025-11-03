"""add_preferences_to_profile

Revision ID: 94cf4cf28bda
Revises: f648ee7ef2ea
Create Date: 2025-11-03 14:19:44.226612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94cf4cf28bda'
down_revision: Union[str, None] = 'f648ee7ef2ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add preferences column to profiles table
    op.add_column('profiles', sa.Column('preferences', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove preferences column from profiles table
    op.drop_column('profiles', 'preferences')