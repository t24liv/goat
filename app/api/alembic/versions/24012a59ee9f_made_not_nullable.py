"""made not nullable

Revision ID: 24012a59ee9f
Revises: df36aeeeaf47
Create Date: 2022-03-22 10:31:25.182139

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
import sqlmodel  



# revision identifiers, used by Alembic.
revision = '24012a59ee9f'
down_revision = 'df36aeeeaf47'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'language_preference',
               existing_type=sa.TEXT(),
               nullable=False,
               schema='customer')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'language_preference',
               existing_type=sa.TEXT(),
               nullable=True,
               schema='customer')
    # ### end Alembic commands ###
