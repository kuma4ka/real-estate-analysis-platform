"""drop Property description

Revision ID: c5f3e4f0g234
Revises: b4e2d3e9f123
Create Date: 2026-05-10 10:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c5f3e4f0g234'
down_revision = 'b4e2d3e9f123'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('properties', schema=None) as batch_op:
        batch_op.drop_column('description')


def downgrade():
    with op.batch_alter_table('properties', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
