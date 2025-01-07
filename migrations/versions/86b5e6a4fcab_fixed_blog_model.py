"""Fixed Blog model

Revision ID: 86b5e6a4fcab
Revises: 6d9c800eaafc
Create Date: 2025-01-07 06:45:05.309025

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86b5e6a4fcab'
down_revision = '6d9c800eaafc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('blog', schema=None) as batch_op:
        batch_op.add_column(sa.Column('book_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'book', ['book_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('blog', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('book_id')

    # ### end Alembic commands ###
