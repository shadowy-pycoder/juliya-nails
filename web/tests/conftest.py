from typing import Generator

from flask import Flask
from flask.testing import FlaskClient
import pytest

import sys
sys.path.append("../web")
from website import create_app, db  # nopep8
from website.models import User, SocialMedia  # nopep8
from test_api.test_users import TESTING_USER  # nopep8


@pytest.fixture(scope='session')
def app() -> Generator:
    app = create_app('testing')
    app_context = app.app_context()
    app_context.push()
    db.Model.metadata.create_all(db.engine)
    user = User(uuid=TESTING_USER, admin=True,
                username='test', email='test@example.com', password='foo1#Bar#')
    db.session.add(user)
    db.session.commit()
    socials = SocialMedia(user_id=user.uuid)
    db.session.add(socials)
    db.session.commit()
    yield app
    db.session.remove()
    db.Model.metadata.drop_all(db.engine)
    app_context.pop()


@pytest.fixture(scope='session')
def client(app: Flask) -> FlaskClient:
    return app.test_client()
