"""Add unique constraint to token_blocklist jti

Revision ID: a3f1c2d84e09
Revises: 14c996f1f805
Create Date: 2026-05-10 10:00:00.000000

"""
from alembic import op


revision = 'a3f1c2d84e09'
down_revision = '14c996f1f805'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('token_blocklist', schema=None) as batch_op:
        batch_op.drop_index('ix_token_blocklist_jti')
        batch_op.create_index(batch_op.f('ix_token_blocklist_jti'), ['jti'], unique=True)


def downgrade():
    with op.batch_alter_table('token_blocklist', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_token_blocklist_jti'))
        batch_op.create_index('ix_token_blocklist_jti', ['jti'], unique=False)
