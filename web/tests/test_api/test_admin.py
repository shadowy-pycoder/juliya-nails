from flask.testing import FlaskClient
import sqlalchemy as sa

from tests.test_api.test_users import TESTING_USER
from website import db
from website.models import SocialMedia, Service, Post, Entry


def test_admin_access(client: FlaskClient) -> None:
    payload = {
        'username': 'user',
        'email': 'user@user.com',
        'password': 'foo#Bar2'
    }
    user = client.post('/api/v1/users', json=payload)
    assert user.status_code == 201
    response = client.post('/api/v1/get-auth-token', auth=('user', 'foo#Bar2'))
    assert response.status_code == 200
    token = response.get_json()['token']
    payload = {'username': 'user42'}
    response = client.put(f'/api/v1/users/{TESTING_USER}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.delete(f'/api/v1/users/{TESTING_USER}',
                             headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.get('/api/v1/socials', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    social = db.session.scalar(sa.select(SocialMedia).filter_by(user_id=TESTING_USER))
    assert social is not None
    response = client.get(f'/api/v1/socials/{social.uuid}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.put(f'/api/v1/socials/{social.uuid}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.get(f'/api/v1/users/{TESTING_USER}/socials',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.put(f'/api/v1/users/{TESTING_USER}/socials',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.post('/api/v1/services',
                           headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    service = db.session.scalar(sa.select(Service).filter_by(name='Test'))
    assert service is not None
    response = client.put(f'/api/v1/services/{service.id}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.delete(f'/api/v1/services/{service.id}',
                             headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.post('/api/v1/posts',
                           headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    post = db.session.scalar(sa.select(Post).filter_by(author_id=TESTING_USER))
    assert post is not None
    response = client.put(f'/api/v1/posts/{post.id}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.delete(f'/api/v1/posts/{post.id}',
                             headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    entry = db.session.scalar(sa.select(Entry).filter_by(user_id=TESTING_USER))
    assert entry is not None
    response = client.get(f'/api/v1/entries/{entry.uuid}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.put(f'/api/v1/entries/{entry.uuid}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.delete(f'/api/v1/entries/{entry.uuid}',
                             headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.put(f'/api/v1/users/{TESTING_USER}/socials/avatar',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.delete(f'/api/v1/users/{TESTING_USER}/socials/avatar',
                             headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.put(f'/api/v1/posts/{post.id}/image',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    response = client.delete(f'/api/v1/posts/{post.id}/image',
                             headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
