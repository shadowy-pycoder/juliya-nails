from datetime import datetime, timedelta

from flask.testing import FlaskClient
import sqlalchemy as sa

from website import db
from website.models import User


def test_pagination(client: FlaskClient, token: str) -> None:
    response = client.get('/api/v1/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    pagination = response.get_json()['pagination']
    assert pagination['page'] == 1
    assert pagination['per_page'] == 25
    response = client.get('/api/v1/users?page=2&per_page=2', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    pagination = response.get_json()['pagination']
    assert pagination['page'] == 2
    assert pagination['per_page'] == 2
    response = client.get('/api/v1/users?page=999&per_page=2', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    pagination = response.get_json()['pagination']
    assert pagination['page'] == pagination['last_page']
    assert pagination['per_page'] == 2
    users = db.session.scalars(sa.select(User)).all()
    assert pagination['total'] == len(users)
    response = client.get('/api/v1/users?page=-1', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400
    response = client.get('/api/v1/users?per_page=999', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400


def test_fields(client: FlaskClient, token: str) -> None:
    response = client.get('/api/v1/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results: list[dict] = response.get_json()['results']
    assert len(results[0]) == 9
    response = client.get('/api/v1/users?fields=uuid,username',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert len(results[0]) == 2
    assert 'uuid' and 'username' in results[0].keys()
    response = client.get('/api/v1/users?fields=foo,bar,uuid,foo,url,',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert len(results[0]) == 2
    assert 'uuid' and 'url' in results[0].keys()


def test_sort(client: FlaskClient, token: str) -> None:
    response = client.get('/api/v1/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results: list[dict] = response.get_json()['results']
    assert all(results[i]['registered_on'] <= results[i+1]['registered_on']
               for i in range(len(results) - 1))
    response = client.get('/api/v1/users?sort=-registered_on',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert all(results[i]['registered_on'] >= results[i+1]['registered_on']
               for i in range(len(results) - 1))
    response = client.get('/api/v1/users?sort=username',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert all(results[i]['username'] <= results[i+1]['username']
               for i in range(len(results) - 1))
    response = client.get('/api/v1/users?sort=-username',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert all(results[i]['username'] >= results[i+1]['username']
               for i in range(len(results) - 1))
    response = client.get('/api/v1/users?sort=foo,bar,-username',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert all(results[i]['username'] >= results[i+1]['username']
               for i in range(len(results) - 1))


def test_filters(client: FlaskClient, token: str) -> None:
    response = client.get('/api/v1/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    response = client.get('/api/v1/users?confirmed=true',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results: list[dict] = response.get_json()['results']
    assert all(results[i]['confirmed'] == True for i in range(len(results)))
    response = client.get('/api/v1/users?confirmed=false',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert all(results[i]['confirmed'] == False for i in range(len(results)))
    response = client.get('/api/v1/users?username=test',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert len(results) == 1 and results[0]['username'] == 'test'
    response = client.get('/api/v1/users?username=somerandomname',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    pagination = response.get_json()['pagination']
    assert len(results) == 0
    assert pagination['total'] == 0
    date = (datetime.now() - timedelta(days=10)).isoformat()
    response = client.get(f'/api/v1/users?registered_on[gt]={date}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert all(results[i]['registered_on'] > date for i in range(len(results)))
    response = client.get(f'/api/v1/users?registered_on[lt]={date}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert all(results[i]['registered_on'] < date for i in range(len(results)))
    response = client.get(f'/api/v1/users?registered_on[gte]={date}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert all(results[i]['registered_on'] >= date for i in range(len(results)))
    response = client.get(f'/api/v1/users?registered_on[lte]={date}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert all(results[i]['registered_on'] <= date for i in range(len(results)))
    date_gte = (datetime.now() - timedelta(days=20)).isoformat()
    response = client.get(f'/api/v1/users?registered_on[lte]={date}&registered_on[gte]={date_gte}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert all(date_gte <= results[i]['registered_on'] <= date for i in range(len(results)))
    response = client.get(f'/api/v1/users?registered_on[gte]={date}&registered_on[lte]={date_gte}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results = response.get_json()['results']
    assert len(results) == 0
    response = client.get(f'/api/v1/users?registered_on[gt]={date}&registered_on[gte]={date_gte}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400
    response = client.get(f'/api/v1/users?registered_on[lt]={date}&registered_on[lte]={date_gte}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400


def test_complex_queries(client: FlaskClient, token: str) -> None:
    response = client.get('/api/v1/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    date = (datetime.now() - timedelta(days=5)).isoformat()
    date_gte = (datetime.now() - timedelta(days=20)).isoformat()
    response = client.get(
        f'/api/v1/users?fields=username,registered_on,confirmed&registered_on[lte]={date}&registered_on[gte]={date_gte}&confirmed=true&sort=username',
        headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    results: list[dict] = response.get_json()['results']
    assert len(results[0]) == 3
    assert 'username' and 'registered_on' and 'confirmed' in results[0].keys()
    assert all(date_gte <= results[i]['registered_on'] <= date for i in range(len(results)))
    assert all(results[i]['confirmed'] == True for i in range(len(results)))
    assert all(results[i]['username'] <= results[i+1]['username'] for i in range(len(results) - 1))
