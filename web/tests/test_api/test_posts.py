import os
import secrets

from apifairy.fields import FileStorage
from flask import current_app
from flask.testing import FlaskClient
import sqlalchemy as sa
from werkzeug.test import TestResponse

from tests.test_api.test_users import TESTING_USER
from website import db
from website.models import Post
from website.utils import delete_image


def test_all_posts(client: FlaskClient, token: str) -> None:
    payload = {
        'title': 'test',
        'content': 'test'
    }
    create_post(client, token, payload)
    response = client.get('/api/v1/posts', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


def test_get_post(client: FlaskClient, token: str) -> None:
    post = db.session.scalar(sa.select(Post).filter_by(title='test'))
    assert post is not None
    response = client.get(f'/api/v1/posts/{post.id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.get_json()['title'] == 'test'
    assert response.get_json()['content'] == 'test'


def test_get_user_posts(client: FlaskClient, token: str) -> None:
    response = client.get(f'api/v1/users/{TESTING_USER}/posts',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


def test_create_post(client: FlaskClient, token: str) -> None:
    response, _ = create_post(client, token)
    assert response.status_code == 201
    post_id = response.get_json()['id']
    assert f'/api/v1/posts/{post_id}' in response.headers['Location']
    invalid_payload = {
        'content': 'string'
    }
    response, _ = create_post(client, token, invalid_payload)
    assert response.status_code == 400


def test_update_post(client: FlaskClient, token: str) -> None:
    payload = {
        'title': 'title',
        'content': 'content',
    }
    post = db.session.scalar(sa.select(Post).filter_by(title='test'))
    assert post is not None
    response = client.put(f'/api/v1/posts/{post.id}', json=payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.get_json()['title'] == 'title'


def test_delete_post(client: FlaskClient, token: str) -> None:
    resp, _ = create_post(client, token)
    post = db.session.scalar(sa.select(Post).filter_by(title=resp.get_json()['title']))
    assert post is not None
    response = client.delete(f'/api/v1/posts/{post.id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 204
    assert response.get_json() is None
    response = client.get(f'/api/v1/services/{post.id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404


def test_update_image(client: FlaskClient, token: str, image_file: FileStorage) -> None:
    post = db.session.scalar(sa.select(Post).filter_by(title='foo'))
    assert post is not None
    old_image = post.image
    response = client.put(f'api/v1/posts/{post.id}/image', data={'image': image_file},
                          headers={
                              'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    new_image = response.get_json()['image']
    assert old_image != new_image
    assert post.image == new_image
    image_path = os.path.join(
        current_app.root_path,
        current_app.config['UPLOAD_FOLDER'], 'posts', new_image)
    assert os.path.exists(image_path)
    delete_image(new_image, path='posts')
    assert not os.path.exists(image_path)


def test_delete_image(client: FlaskClient, token: str, image_file: FileStorage) -> None:
    post = db.session.scalar(sa.select(Post).filter_by(title='foo'))
    assert post is not None
    response = client.put(f'api/v1/posts/{post.id}/image', data={'image': image_file},
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    old_image = response.get_json()['image']
    assert post.image == old_image
    image_path = os.path.join(
        current_app.root_path,
        current_app.config['UPLOAD_FOLDER'], 'posts', old_image)
    assert os.path.exists(image_path)
    response = client.delete(f'api/v1/posts/{post.id}/image', headers={
        'Authorization': f'Bearer {token}'})
    assert response.status_code == 204
    assert post.image is None
    assert not os.path.exists(image_path)


def create_post(
        client: FlaskClient,
        token: str,
        payload: dict | None = None) -> tuple[TestResponse, dict]:
    if payload is None:
        payload = create_post_payload()
    response = client.post('/api/v1/posts', json=payload, headers={'Authorization': f'Bearer {token}'})
    return response, payload


def create_post_payload() -> dict:
    post = secrets.token_hex(8)
    payload = {
        'title': f'title_{post}',
        'content': f'content_{post}'
    }
    return payload
