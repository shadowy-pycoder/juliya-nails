from flask.testing import FlaskClient


def test_no_auth(client: FlaskClient) -> None:
    response = client.get('/api/v1/users')
    assert response.status_code == 401


def test_get_auth_token(client: FlaskClient) -> None:
    response = client.post('/api/v1/get-auth-token', auth=('test', 'foo1#Bar#'))
    assert response.status_code == 200
    token = response.get_json()['token']
    response = client.get('/api/v1/users', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    response = client.get('/api/v1/users', headers={'Authorization': f'Bearer {token[:-1]}'})
    assert response.status_code == 401
