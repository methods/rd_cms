"""2018_04_12_test_views

Revision ID: da02739b6a7f
Revises: 2018_03_22_user_model_refactor
Create Date: 2018-04-12 11:36:07.395067

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da02739b6a7f'
down_revision = '2018_03_22_user_model_refactor'
branch_labels = None
depends_on = None


def upgrade():

    op.get_bind()
    op.execute('''
        CREATE
        MATERIALIZED
        VIEW
        ethnic_groups_by_dimension as (
                SELECT * FROM
            (
            (
                SELECT subtopic.guid AS "subtopic_guid",
            p.guid AS "page_guid",
            p.title AS "page_title",
            p.version AS "page_version",
            p.status AS "page_status",
            p.publication_date AS "page_publication_date",
            p.uri AS "page_uri",
            p.position AS "page_position",
            d.guid AS "dimension_guid",
            d.title AS "dimension_title",
            d.position AS "dimension_position",
            c.title AS "categorisation",
            ethnic_group.value AS "value",
            ethnic_group.position AS "value_position"
            FROM page p
            JOIN page subtopic ON p.parent_guid = subtopic.guid
            JOIN dimension d ON d.page_id = p.guid
            JOIN dimension_categorisation dc ON d.guid = dc.dimension_guid
            JOIN categorisation c ON dc.categorisation_id = c.id
            JOIN association ethnic_group_as_child ON c.id = ethnic_group_as_child.categorisation_id
            JOIN categorisation_value ethnic_group ON ethnic_group_as_child.categorisation_value_id = ethnic_group.id
            )
            UNION
            (
            SELECT subtopic.guid AS "subtopic_guid",
            p.guid AS "page_guid",
            p.title AS "page_title",
            p.version AS "page_version",
            p.status AS "page_status",
            p.publication_date AS "page_publication_date",
            p.uri AS "page_uri",
            p.position AS "page_position",
            d.guid AS "dimension_guid",
            d.title AS "dimension_title",
            d.position AS "dimension_position",
            c.title AS "categorisation",
            ethnic_group.value AS "value",
            ethnic_group.position AS "value_position"
            FROM page p
            JOIN page subtopic ON p.parent_guid = subtopic.guid
            JOIN dimension d ON d.page_id = p.guid
            JOIN dimension_categorisation dc ON d.guid = dc.dimension_guid
            JOIN categorisation c ON dc.categorisation_id = c.id
            JOIN parent_association ethnic_group_as_parent ON c.id = ethnic_group_as_parent.categorisation_id
            JOIN categorisation_value ethnic_group ON ethnic_group_as_parent.categorisation_value_id = ethnic_group.id
            WHERE dc.includes_parents
        )
        ) AS
        all_page_value_connections);
    ''')


def downgrade():
    op.get_bind()
    op.execute('DROP MATERIALIZED VIEW ethnic_groups_by_dimension;')
