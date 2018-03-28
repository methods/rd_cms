"""empty message

Revision ID: 2018_03_22_user_model_refactor
Revises: 2018_03_20_remove_unused_fields
Create Date: 2018-03-22 10:23:42.850491

"""
from alembic import op
import sqlalchemy as sa
from psycopg2._psycopg import ProgrammingError
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# revision identifiers, used by Alembic.
revision = '2018_03_22_user_model_refactor'
down_revision = '2018_03_20_remove_unused_fields'
branch_labels = None
depends_on = None

Session = sessionmaker()
Base = declarative_base()


roles_users = sa.Table('roles_users',
                       Base.metadata,
                       sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
                       sa.Column('role_id', sa.Integer(), sa.ForeignKey('role.id')))


class Role(Base):

    __tablename__ = 'role'

    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.String(255), unique=True)
    description = sa.Column(sa.String(255))


class User(Base):

    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    capabilities = sa.Column(ARRAY(sa.String), default=[])
    roles = relationship('Role', secondary=roles_users)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    session = Session(bind=bind)

    op.add_column('users', sa.Column('capabilities', postgresql.ARRAY(sa.String()), nullable=True))

    users = session.query(User).all()
    for user in users:
        capablities = [role.name for role in user.roles]
        user.capabilities = capablities
        session.add(user)
    session.commit()

    op.drop_table('roles_users')
    op.drop_table('role')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    bind = op.get_bind()
    session = Session(bind=bind)

    from sqlalchemy.schema import Sequence, CreateSequence, DropSequence
    op.execute(DropSequence(Sequence('role_id_seq')))
    op.execute(CreateSequence(Sequence('role_id_seq')))

    op.create_table('role',
                    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('role_id_seq'::regclass)"),
                              nullable=False),
                    sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
                    sa.Column('description', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
                    sa.PrimaryKeyConstraint('id', name='role_pkey'),
                    sa.UniqueConstraint('name', name='role_name_key'),
                    postgresql_ignore_search_path=False
                    )
    op.create_table('roles_users',
                    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
                    sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=True),
                    sa.ForeignKeyConstraint(['role_id'], ['role.id'], name='roles_users_role_id_fkey'),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='roles_users_user_id_fkey')
                    )

    roles = [('ADMIN', 'Application administrator'),
             ('INTERNAL_USER', 'A user in the RDU team who can add, edit and view all pages'),
             ('DEPARTMENTAL_USER', 'A user that can view pages that have a status of departmental review')]

    for r in roles:
        role = Role(name=r[0], description=r[1])
        session.add(role)
        session.commit()

    users = session.query(User).all()
    for user in users:
        for c in user.capabilities:
            r = session.query(Role).filter(Role.name == c).one()
            user.roles.append(r)
        session.add(user)
    session.commit()

    op.drop_column('users', 'capabilities')
    # ### end Alembic commands ###
