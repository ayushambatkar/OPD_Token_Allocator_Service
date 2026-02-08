"""add_date_field_to_slots

Revision ID: a67b0753ff85
Revises: 81b3c50a8c1a
Create Date: 2026-02-01 19:58:03.359178

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a67b0753ff85'
down_revision: Union[str, Sequence[str], None] = '81b3c50a8c1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
