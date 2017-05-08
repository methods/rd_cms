import pytest

from flask import url_for

from application.audit.models import Audit

pytestmark = pytest.mark.usefixtures('mock_user', 'db_session')


def test_user_login_and_logout_recorded(client):

    audit_log = Audit.query.all()

    assert not audit_log

    client.post(
            url_for('security.login'),
            data={'email': 'test@example.com', 'password': 'password123'},
            follow_redirects=True
    )

    audit_log = Audit.query.all()
    assert len(audit_log) == 1
    assert audit_log[0].user == 'test@example.com'
    assert audit_log[0].action == 'login'

    client.get(url_for('security.logout'))

    audit_log = Audit.query.all()
    assert len(audit_log) == 2
    assert audit_log[1].user == 'test@example.com'
    assert audit_log[1].action == 'logout'
