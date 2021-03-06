"""Add style_check to Result.

Revision ID: 92fcfac922f3
Revises: 
Create Date: 2020-12-14 17:03:57.967622

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92fcfac922f3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('result', sa.Column('style_check', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('result', 'style_check')
    # ### end Alembic commands ###
