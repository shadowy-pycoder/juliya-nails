import secrets

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

TESTING_USER = '594d00de-82b0-4ac0-8beb-9b2a9e7c919e'


def test_all_users(client: FlaskClient) -> None:
    response = client.get('/api/v1/users')
    assert response.status_code == 200
    get_response = response.get_json()
    assert get_response['pagination']['total'] == 1
    assert get_response['results'][0]['username'] == 'test'


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


def test_get_user(client: FlaskClient) -> None:
    user_response = client.get(f'/api/v1/users/{TESTING_USER}')
    assert user_response.status_code == 200
    assert user_response.get_json()['username'] == 'test'


def test_me(client: FlaskClient) -> None:
    response = client.get('/api/v1/me')
    assert response.status_code == 200
    assert response.get_json()['username'] == 'test'
    assert 'password' and 'email' not in response.get_json()


def create_user(client: FlaskClient) -> tuple[TestResponse, dict]:
    payload = create_user_payload()
    response = client.post('/api/v1/users', json=payload)
    return response, payload


def create_user_payload() -> dict:
    user = secrets.token_hex(2)
    payload = {
        'username': f'user_{user}',
        'email': f'email_{user}@example.com',
        'password': 'fooBar1%@'
    }
    return payload
