from flask_security import (
    UserMixin,
    RoleMixin
)

from flask_principal import Permission, RoleNeed

from application import db

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    active = db.Column(db.Boolean(), default=True)

    def is_departmental_user(self):
        permissions = [Permission(RoleNeed('DEPARTMENTAL_USER')) for role in self.roles]
        for p in permissions:
            if p.can():
                return True
        else:
            return False

    def is_internal_user(self):
        permissions = [Permission(RoleNeed('INTERNAL_USER')) for role in self.roles]
        for p in permissions:
            if p.can():
                return True
        else:
            return False
