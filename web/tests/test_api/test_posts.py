import secrets

from flask.testing import FlaskClient
import sqlalchemy as sa
from werkzeug.test import TestResponse

from tests.test_api.test_users import TESTING_USER
from website import db
from website.models import Post


def test_all_posts(client: FlaskClient) -> None:
    payload = {
        'title': 'test',
        'content': 'test'
    }
    create_post(client, payload)
    response = client.get('/api/v1/posts')
    assert response.status_code == 200


def test_get_post(client: FlaskClient) -> None:
    post = db.session.scalar(sa.select(Post).filter_by(title='test'))
    assert post is not None
    response = client.get(f'/api/v1/posts/{post.id}')
    assert response.status_code == 200
    assert response.get_json()['title'] == 'test'
    assert response.get_json()['content'] == 'test'


def test_get_user_posts(client: FlaskClient) -> None:
    response = client.get(f'api/v1/users/{TESTING_USER}/posts')
    assert response.status_code == 200


def test_create_post(client: FlaskClient) -> None:
    response, _ = create_post(client)
    assert response.status_code == 201
    invalid_payload = {
        'content': 'string'
    }
    response, _ = create_post(client, invalid_payload)
    assert response.status_code == 400


def test_update_post(client: FlaskClient) -> None:
    payload = {
        'title': 'title',
        'content': 'content',
    }
    post = db.session.scalar(sa.select(Post).filter_by(title='test'))
    assert post is not None
    response = client.put(f'/api/v1/posts/{post.id}', json=payload)
    assert response.status_code == 200
    assert response.get_json()['title'] == 'title'


def test_delete_post(client: FlaskClient) -> None:
    resp, _ = create_post(client)
    post = db.session.scalar(sa.select(Post).filter_by(title=resp.get_json()['title']))
    assert post is not None
    response = client.delete(f'/api/v1/posts/{post.id}')
    assert response.status_code == 204
    assert response.get_json() is None
    response = client.get(f'/api/v1/services/{post.id}')
    assert response.status_code == 404


def create_post(
        client: FlaskClient,
        payload: dict | None = None) -> tuple[TestResponse, dict]:
    if payload is None:
        payload = create_post_payload()
    response = client.post('/api/v1/posts', json=payload)
    return response, payload


def create_post_payload() -> dict:
    post = secrets.token_hex(8)
    payload = {
        'title': f'title_{post}',
        'content': f'content_{post}'
    }
    return payload
