import secrets

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from website import db
from website.models import User

TESTING_USER = '594d00de-82b0-4ac0-8beb-9b2a9e7c919e'


def test_all_users(client: FlaskClient) -> None:
    populate_users(2)
    db.session.commit()
    response = client.get('/api/v1/users')
    assert response.status_code == 200
    get_response = response.get_json()
    assert get_response['pagination']['total'] == 3


def test_create_user(client: FlaskClient) -> None:
    response, payload = create_user(client)
    assert response.status_code == 201
    post_response = response.get_json()
    assert payload['username'] == post_response['username']
    assert post_response['uuid'] in response.headers['Location']
    social_response = client.get(post_response['socials'])
    assert social_response.status_code == 200
    user_response = client.get(post_response['url'])
    assert user_response.status_code == 200
    assert payload['username'] == user_response.get_json()['username']


def test_create_invalid_user(client: FlaskClient) -> None:
    invalid_payload = {
        'username': 'test',
        'email': 'broken@@example.com',
        'password': 'foo'
    }
    response, _ = create_user(client, invalid_payload)
    assert response.status_code == 400
    assert len(response.get_json()['errors']['json']) == 3


def test_get_user(client: FlaskClient) -> None:
    user_response = client.get(f'/api/v1/users/{TESTING_USER}')
    assert user_response.status_code == 200
    assert user_response.get_json()['username'] == 'test'


def test_me(client: FlaskClient) -> None:
    response = client.get('/api/v1/me')
    assert response.status_code == 200
    assert response.get_json()['username'] == 'test'
    assert 'password' and 'email' not in response.get_json()


def test_update_me(client: FlaskClient) -> None:
    payload = {
        'old_password': 'foo#Bar#',
        'password': 'foo#Bar#2',
        'email': 'user@example.com'
    }
    response = client.put('/api/v1/me', json=payload)
    assert response.status_code == 200
    assert response.get_json()['username'] == 'test'

    invalid_payload = {
        'username': 'test',
        'email': 'user@example.com'
    }
    response = client.put('/api/v1/me', json=invalid_payload)
    assert response.status_code == 400
    assert response.get_json()['errors']['json']['username'] == ['Unknown field.']

    invalid_payload = {
        'password': 'foo#Bar#2'
    }
    response = client.put('/api/v1/me', json=invalid_payload)
    assert response.status_code == 400
    invalid_payload = {
        'old_password': 'foo#Bar#2'
    }
    response = client.put('/api/v1/me', json=invalid_payload)
    assert response.status_code == 400


def create_user_payload() -> dict:
    user = secrets.token_hex(4)
    payload = {
        'username': f'u_{user}',
        'email': f'email_{user}@example.com',
        'password': 'fooBar1%@'
    }
    return payload


def create_user(
        client: FlaskClient,
        payload: dict | None = None) -> tuple[TestResponse, dict]:
    if payload is None:
        payload = create_user_payload()
    response = client.post('/api/v1/users', json=payload)
    return response, payload


def populate_user(payload: dict | None = None) -> None:
    if payload is None:
        payload = create_user_payload()
    db.session.add(User(**payload))


def populate_users(num: int) -> None:
    for _ in range(num):
        populate_user()
