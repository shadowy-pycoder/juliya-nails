import secrets

from flask.testing import FlaskClient
from werkzeug.test import TestResponse


TESTING_USER = '594d00de-82b0-4ac0-8beb-9b2a9e7c919e'


def test_all_users(client: FlaskClient, token: str) -> None:
    response = client.get('/api/v1/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    get_response = response.get_json()
    assert get_response['pagination']['total'] > 0


def test_create_user(client: FlaskClient, token: str) -> None:
    response, payload = create_user(client)
    assert response.status_code == 201
    post_response = response.get_json()
    assert payload['username'] == post_response['username']
    assert post_response['uuid'] in response.headers['Location']
    social_response = client.get(post_response['socials'], headers={'Authorization': f'Bearer {token}'})
    assert social_response.status_code == 200
    user_response = client.get(post_response['url'], headers={'Authorization': f'Bearer {token}'})
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


def test_get_user(client: FlaskClient, token: str) -> None:
    user_response = client.get(f'/api/v1/users/{TESTING_USER}', headers={'Authorization': f'Bearer {token}'})
    assert user_response.status_code == 200
    assert user_response.get_json()['username'] == 'test'


def test_me(client: FlaskClient, token: str) -> None:
    response = client.get('/api/v1/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.get_json()['username'] == 'test'
    assert 'password' and 'email' not in response.get_json()


def test_update_me(client: FlaskClient, token: str) -> None:
    payload = {
        'old_password': 'foo1#Bar#',
        'password': 'foo#Bar#2',
        'email': 'user@example.com'
    }
    response = client.put('/api/v1/me', json=payload, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.get_json()['username'] == 'test'

    invalid_payload = {
        'username': 'test',
        'email': 'user@example.com'
    }
    response = client.put('/api/v1/me', json=invalid_payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400
    assert response.get_json()['errors']['json']['username'] == ['Unknown field.']

    invalid_payload = {
        'password': 'foo#Bar#2'
    }
    response = client.put('/api/v1/me', json=invalid_payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400
    invalid_payload = {
        'old_password': 'foo#Bar#2'
    }
    response = client.put('/api/v1/me', json=invalid_payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400


def test_update_admin(client: FlaskClient, token: str) -> None:
    payload = {
        'admin': True,
        'registered_on': '2023-04-24 14:15',
        'confirmed_on': '2023-04-24 14:15',
        'confirmed': True,
        'email': 'upduser@example.com',
        'username': 'test2',
        'password': 'foo#barR1'
    }
    response = client.put(f'/api/v1/users/{TESTING_USER}', json=payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.get_json()['username'] == payload['username']
    assert response.get_json()['email'] == payload['email']

    invalid_payload = {
        'email': 'upduser@example.com',
        'username': 'test2test2test2test2test2',
    }
    response = client.put(f'/api/v1/users/{TESTING_USER}', json=invalid_payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400


def test_delete_user(client: FlaskClient, token: str) -> None:
    payload = {
        'username': 'delete',
        'email': 'delete@delete.com',
        'password': 'dElet1e@'
    }
    user_response, _ = create_user(client, payload)
    uuid = user_response.get_json()['uuid']
    response = client.delete(f'/api/v1/users/{uuid}',
                             headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 204
    assert response.get_json() is None
    response = client.get(f'/api/v1/users/{uuid}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404
    response = client.delete(f'/api/v1/users/{TESTING_USER}',
                             headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403


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
