"""Add automation tracking fields to Resultado and validation field to CasoPrueba

Revision ID: 3a8b9f0c1d2e
Revises: 2f749fedc46b
Create Date: 2026-05-31 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '3a8b9f0c1d2e'
down_revision = '2f749fedc46b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('resultado', schema=None) as batch_op:
        batch_op.add_column(sa.Column('modo_ejecucion', sa.Enum('manual', 'automatizado', name='modo_ejecucion'), nullable=False, server_default='manual'))
        batch_op.add_column(sa.Column('estado_ejecucion', sa.Enum('pendiente', 'en_progreso', 'completado', 'error', name='estado_ejecucion'), nullable=False, server_default='completado'))
        batch_op.add_column(sa.Column('jenkins_build_number', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('jenkins_log_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('tiempo_inicio_jenkins', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('tiempo_fin_jenkins', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('numero_intentos', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('json_respuesta_jenkins', sa.JSON(), nullable=True))

    with op.batch_alter_table('caso_prueba', schema=None) as batch_op:
        batch_op.add_column(sa.Column('requiere_intento_manual', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table('caso_prueba', schema=None) as batch_op:
        batch_op.drop_column('requiere_intento_manual')

    with op.batch_alter_table('resultado', schema=None) as batch_op:
        batch_op.drop_column('json_respuesta_jenkins')
        batch_op.drop_column('numero_intentos')
        batch_op.drop_column('tiempo_fin_jenkins')
        batch_op.drop_column('tiempo_inicio_jenkins')
        batch_op.drop_column('jenkins_log_url')
        batch_op.drop_column('jenkins_build_number')
        batch_op.drop_column('estado_ejecucion')
        batch_op.drop_column('modo_ejecucion')
