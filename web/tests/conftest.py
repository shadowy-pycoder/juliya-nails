from datetime import datetime, timedelta
import os
import random
from typing import Generator

from apifairy.fields import FileStorage
from flask import Flask, current_app
from flask.testing import FlaskClient
import pytest

from .test_api.test_users import TESTING_USER
from website import create_app, db
from website.models import User, SocialMedia, Service, Post, Entry


@pytest.fixture(scope='session')
def app() -> Generator:
    app = create_app('testing')
    app_context = app.app_context()
    app_context.push()
    db.Model.metadata.drop_all(db.engine)
    db.Model.metadata.create_all(db.engine)
    users = []
    user = User(uuid=TESTING_USER, admin=True, confirmed=True, confirmed_on='2023-03-27 15:00',
                username='test', email='test@example.com', password='foo1#Bar#')
    users.append(user)
    for i in range(10):
        days = random.randint(1, 31)
        hours = random.randint(0, 23)
        users.append(User(username=f'user_{i}',
                          email=f'user_{i}@example.com',
                          password='foo1#Bar#',
                          confirmed=random.choice([True, False]),
                          confirmed_on=datetime.now()-timedelta(hours=hours),
                          registered_on=datetime.now()-timedelta(days=days, hours=hours)))
    db.session.add_all(users)
    db.session.commit()
    service = Service(id=77, name='Test', duration=3)
    db.session.add(service)
    db.session.commit()
    entry = Entry(user_id=user.uuid, date='2023-08-25', time='10:00')
    socials = SocialMedia(user_id=user.uuid)
    post = Post(author_id=user.uuid, title='foo', content='bar')
    db.session.add(entry)
    db.session.add(socials)
    db.session.add(post)
    db.session.commit()
    yield app
    db.session.remove()
    db.Model.metadata.drop_all(db.engine)
    app_context.pop()


@pytest.fixture(scope='session')
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture(scope='session')
def token(client: FlaskClient) -> str:
    response = client.post('/api/v1/get-auth-token', auth=('test', 'foo1#Bar#'))
    token = response.get_json()['token']
    return token


@pytest.fixture(scope='session')
def image_file() -> Generator[FileStorage, None, None]:
    file_path = os.path.join(
        current_app.root_path,
        current_app.config['UPLOAD_FOLDER'], 'profiles',
        current_app.config['DEFAULT_AVATAR'])
    file = FileStorage(stream=open(file_path, 'rb'),
                       filename=current_app.config['DEFAULT_AVATAR'],
                       content_type='image/jpeg')
    try:
        yield file
    finally:
        file.close()
