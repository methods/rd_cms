"""empty message

Revision ID: c0dc0cf68e07
Revises: 2019_04_16_drop_published_bool
Create Date: 2019-04-18 15:23:51.211497

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_topic_short_title'
down_revision = '2019_04_16_drop_published_bool'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topic', sa.Column('short_title', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('topic', 'short_title')
    # ### end Alembic commands ###
