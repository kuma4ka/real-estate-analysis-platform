"""alter users.role from String to Enum

Revision ID: 6fefc9b8a496
Revises: c5f3e4f0g234
Create Date: 2026-05-18 21:44:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '6fefc9b8a496'
down_revision = 'c5f3e4f0g234'
branch_labels = None
depends_on = None

# Allowed values as a plain tuple so we don't need to import the app's enum.
_ROLE_VALUES = ('Admin', 'Analyst', 'User', 'Guest')


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'role',
            existing_type=sa.String(20),
            type_=sa.Enum(*_ROLE_VALUES, name='user_role_enum', native_enum=False),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'role',
            existing_type=sa.Enum(*_ROLE_VALUES, name='user_role_enum', native_enum=False),
            type_=sa.String(20),
            existing_nullable=False,
        )
