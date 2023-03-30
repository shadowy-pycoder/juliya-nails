from flask import current_app, jsonify, g
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from flask.wrappers import Response
import sqlalchemy as sa
from werkzeug.exceptions import Unauthorized, Forbidden

from . import api
from ... import db
from ...models import User

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


@basic_auth.verify_password
def verify_password(username: str, password: str) -> User | None:
    if username and password:
        user = db.session.scalar(sa.select(User).filter_by(username=username))
        if not user:
            user = db.session.scalar(sa.select(User).filter_by(email=username))
        if user and user.verify_password(password):
            return user
    return None


@basic_auth.error_handler
def basic_auth_error(status: int = 401) -> Response:
    error = (Forbidden if status == 403 else Unauthorized)()
    response = jsonify({
        'code': error.code,
        'message': error.name,
        'description': error.description,
    }, error.code, {'WWW-Authenticate': 'Form'})
    return response


@token_auth.verify_token
def verify_token(token):
    if token:
        return User.confirm_email_token()


@token_auth.error_handler
def token_auth_error(status=401):
    error = (Forbidden if status == 403 else Unauthorized)()
    return {
        'code': error.code,
        'message': error.name,
        'description': error.description,
    }, error.code
