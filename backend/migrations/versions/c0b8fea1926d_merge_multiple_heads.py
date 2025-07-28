"""merge_multiple_heads

Revision ID: c0b8fea1926d
Revises: add_company_info_to_session_fixed, remove_crawling_fields_001
Create Date: 2025-07-28 17:55:47.750964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0b8fea1926d'
down_revision: Union[str, None] = ('add_company_info_to_session_fixed', 'remove_crawling_fields_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
