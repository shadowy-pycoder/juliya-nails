import secrets

from flask.testing import FlaskClient
import sqlalchemy as sa
from werkzeug.test import TestResponse

from website import db
from website.models import Service


def test_all_services(client: FlaskClient, token: str) -> None:
    response = client.get('/api/v1/services', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.get_json()['results'][0]['name'] == 'Test'


def test_get_service(client: FlaskClient, token: str) -> None:
    service = db.session.scalar(sa.select(Service).filter_by(name='Test'))
    assert service is not None
    response = client.get(f'/api/v1/services/{service.id}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.get_json()['name'] == 'Test'
    assert response.get_json()['duration'] == '3.0'


def test_create_service(client: FlaskClient, token: str) -> None:
    response, payload = create_service(client, token)
    assert response.status_code == 201
    service_id = response.get_json()['id']
    assert f'/api/v1/services/{service_id}' in response.headers['Location']
    invalid_payload = {
        'name': payload['name'],
        'duration': 2
    }
    response, _ = create_service(client, token, invalid_payload)
    assert response.status_code == 400


def test_update_service(client: FlaskClient, token: str) -> None:
    payload = {
        'name': 'test3',
        'duration': '3.5',
    }
    service = db.session.scalar(sa.select(Service).filter_by(name='Test'))
    assert service is not None
    response = client.put(f'/api/v1/services/{service.id}', json=payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.get_json()['name'] == 'Test3'
    invalid_payload = {
        'name': 'test3',
    }
    response = client.put(f'/api/v1/services/{service.id}', json=invalid_payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400


def test_delete_service(client: FlaskClient, token: str) -> None:
    resp, _ = create_service(client, token)
    service = db.session.scalar(sa.select(Service).filter_by(name=resp.get_json()['name']))
    assert service is not None
    response = client.delete(f'/api/v1/services/{service.id}',
                             headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 204
    assert response.get_json() is None
    response = client.get(f'/api/v1/services/{service.id}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404


def create_service(
        client: FlaskClient,
        token: str,
        payload: dict | None = None) -> tuple[TestResponse, dict]:
    if payload is None:
        payload = create_service_payload()
    response = client.post('/api/v1/services', json=payload,
                           headers={'Authorization': f'Bearer {token}'})
    return response, payload


def create_service_payload() -> dict:
    service = secrets.token_hex(4)
    payload = {
        'duration': secrets.randbits(3) + 1,
        'name': f'service_{service}'
    }
    return payload
