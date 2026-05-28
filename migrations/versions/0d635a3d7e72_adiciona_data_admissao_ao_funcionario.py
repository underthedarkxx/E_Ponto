"""adiciona data_admissao ao funcionario

Revision ID: 0d635a3d7e72
Revises: 70275fbd7283
Create Date: 2026-05-26 20:33:43.844344

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d635a3d7e72'
down_revision = '70275fbd7283'
branch_labels = None
depends_on = None


def upgrade():
    # Adiciona apenas a coluna data_admissao. A "mudanca de tipo" em
    # registros.tipo que o autogenerate sugeriu foi removida de proposito:
    # no SQLite o enum e' armazenado como texto (sem enforcement), entao a
    # alteracao seria um no-op que so recriaria a tabela de registros
    # (que carrega a cadeia de hash) sem necessidade.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('data_admissao', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('data_admissao')
