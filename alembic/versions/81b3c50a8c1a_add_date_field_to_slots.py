"""add_date_field_to_slots

Revision ID: 81b3c50a8c1a
Revises: 7f3f845d9377
Create Date: 2026-02-01 18:33:35.374051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81b3c50a8c1a'
down_revision: Union[str, Sequence[str], None] = '7f3f845d9377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
