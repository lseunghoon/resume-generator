"""Add company_info field to sessions table

Revision ID: add_company_info_to_session_fixed
Revises: fd819a32a6bd
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_company_info_to_session_fixed'
down_revision = 'fd819a32a6bd'
branch_labels = None
depends_on = None

def upgrade():
    """Add company_info column to sessions table"""
    op.add_column('sessions', sa.Column('company_info', sa.Text(), nullable=True))

def downgrade():
    """Remove company_info column from sessions table"""
    op.drop_column('sessions', 'company_info')