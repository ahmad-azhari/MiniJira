"""add ejecucion_ciclo table

Revision ID: add_ejecucion_ciclo_table
Revises: 3a8b9f0c1d2e
Create Date: 2026-06-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from config.constantes import EstadoEjecucionEnum

revision = 'add_ejecucion_ciclo_table'
down_revision = '3a8b9f0c1d2e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ejecucion_ciclo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ciclo_prueba_id', sa.Integer(), sa.ForeignKey('ciclo_prueba.id'), nullable=False),
        sa.Column('fecha_ejecucion', sa.DateTime(), default=sa.func.now()),
        sa.Column('total_pruebas', sa.Integer(), default=0),
        sa.Column('pruebas_pasadas', sa.Integer(), default=0),
        sa.Column('pruebas_fallidas', sa.Integer(), default=0),
        sa.Column('pruebas_en_progreso', sa.Integer(), default=0),
        sa.Column('estado_ejecucion', sa.Enum(EstadoEjecucionEnum), default=EstadoEjecucionEnum.COMPLETADO),
        sa.Column('jenkins_build_number', sa.Integer(), nullable=True),
        sa.Column('id_solicitud', sa.String(255), nullable=True),
    )


def downgrade():
    op.drop_table('ejecucion_ciclo')
