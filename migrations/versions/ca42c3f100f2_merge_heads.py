"""merge heads

Revision ID: ca42c3f100f2
Revises: add_ejecucion_ciclo_table, d0d5f8e4a151
Create Date: 2026-06-02 11:31:45.452596

"""
from alembic import op
import sqlalchemy as sa


revision = 'ca42c3f100f2'
down_revision = ('add_ejecucion_ciclo_table', 'd0d5f8e4a151')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
