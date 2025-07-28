"""Remove crawling fields and add job info fields

Revision ID: remove_crawling_fields_001
Revises: e97c2851938c
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'remove_crawling_fields_001'
down_revision = 'e97c2851938c'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema"""
    # 1. 새로운 필드들 추가
    op.add_column('sessions', sa.Column('company_name', sa.String(length=255), nullable=True))
    op.add_column('sessions', sa.Column('job_title', sa.String(length=255), nullable=True))
    op.add_column('sessions', sa.Column('main_responsibilities', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('requirements', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('preferred_qualifications', sa.Text(), nullable=True))
    
    # 2. 기존 jd_url 필드 제거 (크롤링 관련)
    op.drop_column('sessions', 'jd_url')


def downgrade():
    """Downgrade database schema"""
    # 1. jd_url 필드 복원
    op.add_column('sessions', sa.Column('jd_url', sa.Text(), nullable=True))
    
    # 2. 새로운 필드들 제거
    op.drop_column('sessions', 'preferred_qualifications')
    op.drop_column('sessions', 'requirements')
    op.drop_column('sessions', 'main_responsibilities')
    op.drop_column('sessions', 'job_title')
    op.drop_column('sessions', 'company_name') 