"""
Update topic meta descriptions

Revision ID: 2020_05_19_update_topics
Revises: 915fdaf7e1c3
Create Date: 2020-05-19 14:02:04.242855

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2020_05_19_update_topics"
down_revision = "915fdaf7e1c3"
branch_labels = None
depends_on = None

update_topics = """
UPDATE topic
SET meta_description = 'Statistics on crime, policing, sentencing and prison, analysed by ethnicity, age,
 gender and other factors.'
WHERE slug = 'crime-justice-and-the-law';

UPDATE topic
SET meta_description = 'Statistics on participation in cultural and community activities, analysed by ethnicity, age,
    gender and other factors.'
WHERE slug = 'culture-and-community';

UPDATE topic
SET meta_description = 'Statistics on school results, apprenticeships and degrees, and what people do after studying,
 analysed by ethnicity, gender and other factors.'
WHERE slug = 'education-skills-and-training';

UPDATE topic
SET meta_description = 'Statistics on physical and mental health, analysed by ethnicity, age, gender and other factors.'
WHERE slug = 'health';

UPDATE topic
SET meta_description = 'Statistics on housing, home ownership, social housing and homelessness, analysed by ethnicity,
 age, gender and other factors.'
WHERE slug = 'housing';

UPDATE topic
SET meta_description = 'UK population statistics, analysed by ethnicity, age, gender and other factors.'
WHERE slug = 'uk-population-by-ethnicity';

UPDATE topic
SET meta_description = 'uk-population-by-ethnicity'
WHERE slug = 'uk-population-by-ethnicity';

UPDATE topic
SET meta_description = 'UK employment and income statistics, analysed by ethnicity, age, gender and other factors.'
WHERE slug = 'work-pay-and-benefits';

UPDATE topic
SET meta_description = 'Statistics on ethnic diversity and pay in schools, NHS and other public services, analysed by
 ethnicity, age, gender and other factors.'
WHERE slug = 'workforce-and-business';
"""


def upgrade():
    op.execute(update_topics)


def downgrade():
    op.execute(update_topics)
