"""drop Source table

Revision ID: b4e2d3e9f123
Revises: a3f1c2d84e09
Create Date: 2026-05-10 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b4e2d3e9f123'
down_revision = 'a3f1c2d84e09'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('sources')


def downgrade():
    op.create_table('sources',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('base_url', sa.Text(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
