"""renamed poi column to uid

Revision ID: e4dbb9cad692
Revises: c8a4691be513
Create Date: 2022-03-10 14:29:51.429857

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
import sqlmodel  



# revision identifiers, used by Alembic.
revision = 'e4dbb9cad692'
down_revision = 'c8a4691be513'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reached_poi_heatmap', sa.Column('poi_uid', sa.Integer(), nullable=False), schema='customer')
    op.drop_constraint('reached_poi_heatmap_poi_id_fkey', 'reached_poi_heatmap', schema='customer', type_='foreignkey')
    op.create_foreign_key(None, 'reached_poi_heatmap', 'poi', ['poi_uid'], ['id'], source_schema='customer', referent_schema='basic', ondelete='CASCADE')
    op.drop_column('reached_poi_heatmap', 'poi_id', schema='customer')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reached_poi_heatmap', sa.Column('poi_id', sa.INTEGER(), autoincrement=False, nullable=False), schema='customer')
    op.drop_constraint(None, 'reached_poi_heatmap', schema='customer', type_='foreignkey')
    op.create_foreign_key('reached_poi_heatmap_poi_id_fkey', 'reached_poi_heatmap', 'poi', ['poi_id'], ['id'], source_schema='customer', referent_schema='basic', ondelete='CASCADE')
    op.drop_column('reached_poi_heatmap', 'poi_uid', schema='customer')
    # ### end Alembic commands ###