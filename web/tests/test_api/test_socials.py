from flask.testing import FlaskClient
import sqlalchemy as sa


from tests.test_api.test_users import TESTING_USER
from website import db
from website.models import SocialMedia


def test_all_socials(client: FlaskClient, token: str) -> None:
    response = client.get('/api/v1/socials', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


def test_get_social(client: FlaskClient, token: str) -> None:
    social = db.session.scalar(sa.select(SocialMedia).filter_by(user_id=TESTING_USER))
    assert social is not None
    response = client.get(f'/api/v1/socials/{social.uuid}',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


def test_my_socials(client: FlaskClient, token: str) -> None:
    response = client.get('api/v1/me/socials', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.get_json()['user']['uuid'] == TESTING_USER


def test_get_user_socials(client: FlaskClient, token: str) -> None:
    response = client.get(f'api/v1/users/{TESTING_USER}/socials',
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


def test_update_my_socials(client: FlaskClient, token: str) -> None:
    payload = {
        "viber": "+99999999999",
        "website": "https://www.example.com/",
        "instagram": "https://instagram.com/username",
        "telegram": "https://t.me/username",
        "about": "string",
        "youtube": "https://www.youtube.com/channel/",
        "phone_number": "+99999999999",
        "vk": "https://vk.com/username",
        "first_name": "John",
        "whatsapp": "+99999999999",
        "last_name": "Doe"
    }
    response = client.put('api/v1/me/socials', json=payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    invalid_payload = {
        "viber": "string",
        "website": "string",
        "instagram": "https://www.example.com/",
        "telegram": "https://www.example.com/",
        "youtube": "https://www.example.com/",
        "phone_number": "string",
        "vk": "https://www.example.com/",
        "first_name": "john",
        "whatsapp": "string",
        "last_name": "doe"
    }
    response = client.put('api/v1/me/socials', json=invalid_payload,
                          headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400
    assert len(response.get_json()['errors']['json']) == len(invalid_payload)
