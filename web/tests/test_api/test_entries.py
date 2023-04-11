import random

from flask.testing import FlaskClient
import sqlalchemy as sa
from werkzeug.test import TestResponse

from tests.test_api.test_users import TESTING_USER
from website import db
from website.models import Entry, Service


def test_all_entries(client: FlaskClient, token: str) -> None:
    prev_payload = {
        'date': '2023-08-24',
        'time': '8:00'
    }
    next_payload = {
        'date': '2023-08-24',
        'time': '15:00'
    }
    prev_entry = Entry(user_id=TESTING_USER, **prev_payload)
    next_entry = Entry(user_id=TESTING_USER, **next_payload)
    service = db.session.get(Service, 77)
    assert service is not None
    prev_entry.services.append(service)
    next_entry.services.append(service)
    db.session.add_all([prev_entry, next_entry])
    db.session.commit()
    response = client.get('/api/v1/entries', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


def test_get_entry(client: FlaskClient, token: str) -> None:
    entry = db.session.scalar(sa.select(Entry).filter_by(user_id=TESTING_USER))
    assert entry is not None
    response = client.get(f'/api/v1/entries/{entry.uuid}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


def test_create_entry(client: FlaskClient, token: str) -> None:
    payload = {
        'date': '2023-08-24',
        'time': '11:00',
        'services': [77,]
    }
    invalid_payload_prev = {
        'date': '2023-08-24',
        'time': '10:00',
        'services': [77,]
    }
    invalid_payload_next = {
        'date': '2023-08-24',
        'time': '14:00',
        'services': [77,]
    }
    with db.session.no_autoflush:
        response, _ = create_entry(client, token, payload)
        response_prev, _ = create_entry(client, token, invalid_payload_prev)
        response_next, _ = create_entry(client, token, invalid_payload_next)
        db.session.close()
    assert response.status_code == 201
    entry_id = response.get_json()['uuid']
    assert f'/api/v1/entries/{entry_id}' in response.headers['Location']
    assert response_prev.status_code == 400
    assert response_next.status_code == 400


def test_update_entry(client: FlaskClient, token: str) -> None:
    payload = {
        'date': '2023-08-24',
        'time': '12:00',
    }
    invalid_payload_prev = {
        'date': '2023-08-24',
        'time': '09:00',
    }
    invalid_payload_next = {
        'date': '2023-08-24',
        'time': '15:00',
    }
    entry = db.session.scalar(sa.select(Entry).filter(Entry.user_id == TESTING_USER, Entry.time == '11:00'))
    assert entry is not None
    response = client.put(f'/api/v1/entries/{entry.uuid}', json=payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    response_prev = client.put(f'/api/v1/entries/{entry.uuid}', json=invalid_payload_prev,
                               headers={'Authorization': f'Bearer {token}'})
    assert response_prev.status_code == 400
    response_next = client.put(f'/api/v1/entries/{entry.uuid}', json=invalid_payload_next,
                               headers={'Authorization': f'Bearer {token}'})
    assert response_next.status_code == 400


def test_get_user_entries(client: FlaskClient, token: str) -> None:
    response = client.get(f'api/v1/users/{TESTING_USER}/entries',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


def test_get_service_entries(client: FlaskClient, token: str) -> None:
    service = db.session.get(Service, 77)
    assert service is not None
    response = client.get(f'api/v1/services/{service.id}/entries',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


def test_my_entries(client: FlaskClient, token: str) -> None:
    response = client.get('api/v1/me/entries', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    for result in response.get_json()['results']:
        assert result['user']['uuid'] == TESTING_USER


def test_delete_entry(client: FlaskClient, token: str) -> None:
    entry = db.session.scalar(sa.select(Entry).filter_by(user_id=TESTING_USER))
    assert entry is not None
    response = client.delete(f'/api/v1/entries/{entry.uuid}',
                             headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 204
    response = client.get(f'/api/v1/entries/{entry.uuid}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404


def create_entry(
        client: FlaskClient,
        token: str,
        payload: dict | None = None) -> tuple[TestResponse, dict]:
    if payload is None:
        payload = create_entry_payload()
    response = client.post('/api/v1/entries', json=payload, headers={'Authorization': f'Bearer {token}'})
    return response, payload


def create_entry_payload() -> dict:
    hour = random.randint(0, 23)
    minutes = random.choice([0, 3])
    payload = {
        'date': '2023-08-24',
        'time': f'{hour}:{minutes}0',
    }
    return payload
