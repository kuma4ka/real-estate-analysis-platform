"""add indexes on property city is_active price rooms source_website and tokenblocklist created_at

Revision ID: a1b2c3d4e5f6
Revises: 6fefc9b8a496
Create Date: 2026-06-04 18:00:00.000000

"""
from alembic import op

revision = 'a1b2c3d4e5f6'
down_revision = '6fefc9b8a496'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_properties_city', 'properties', ['city'], unique=False)
    op.create_index('ix_properties_is_active', 'properties', ['is_active'], unique=False)
    op.create_index('ix_properties_price', 'properties', ['price'], unique=False)
    op.create_index('ix_properties_rooms', 'properties', ['rooms'], unique=False)
    op.create_index('ix_properties_source_website', 'properties', ['source_website'], unique=False)
    op.create_index('ix_properties_active_city', 'properties', ['is_active', 'city'], unique=False)
    op.create_index('ix_properties_active_created', 'properties', ['is_active', 'created_at'], unique=False)
    op.create_index('ix_token_blocklist_created_at', 'token_blocklist', ['created_at'], unique=False)


def downgrade():
    op.drop_index('ix_properties_city', table_name='properties')
    op.drop_index('ix_properties_is_active', table_name='properties')
    op.drop_index('ix_properties_price', table_name='properties')
    op.drop_index('ix_properties_rooms', table_name='properties')
    op.drop_index('ix_properties_source_website', table_name='properties')
    op.drop_index('ix_properties_active_city', table_name='properties')
    op.drop_index('ix_properties_active_created', table_name='properties')
    op.drop_index('ix_token_blocklist_created_at', table_name='token_blocklist')
