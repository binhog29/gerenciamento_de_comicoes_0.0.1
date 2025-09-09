"""Criação inicial do banco de dados

Revision ID: ffd8bdb52191
Revises: 
Create Date: 2025-09-08 22:30:00.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffd8bdb52191' # Este ID é apenas um marcador
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### Tabela de Utilizadores ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=150), nullable=False),
    sa.Column('password_hash', sa.String(length=150), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    # ### Tabela de Instalações ###
    op.create_table('instalacao',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tipo_combo', sa.String(length=50), nullable=False),
    sa.Column('descricao_combo', sa.String(length=100), nullable=False),
    sa.Column('valor_original', sa.Float(), nullable=False),
    sa.Column('valor_arredondado', sa.Float(), nullable=False),
    sa.Column('login_cliente', sa.String(length=100), nullable=False),
    sa.Column('data_instalacao', sa.String(length=20), nullable=False),
    sa.Column('porcentagem_comissao', sa.Float(), nullable=False),
    sa.Column('comissao', sa.Float(), nullable=False),
    sa.Column('observacoes', sa.String(length=300), nullable=True),
    sa.Column('data_registro', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_instalacao_user_id'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### Tabela de Relatórios Históricos ###
    op.create_table('relatorio_historico',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('data_inicio', sa.String(length=20), nullable=False),
    sa.Column('data_fim', sa.String(length=20), nullable=False),
    sa.Column('total_comissoes', sa.Float(), nullable=False),
    sa.Column('num_instalacoes', sa.Integer(), nullable=False),
    sa.Column('data_salva', sa.DateTime(), nullable=True),
    sa.Column('instalacoes_json', sa.String(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_relatorio_historico_user_id'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('relatorio_historico')
    op.drop_table('instalacao')
    op.drop_table('user')