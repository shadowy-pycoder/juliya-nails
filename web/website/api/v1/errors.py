from flask import jsonify, current_app, Blueprint
from flask.wrappers import Response
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException, InternalServerError, Unauthorized, Forbidden

from ... import basic_auth, token_auth

for_errors = Blueprint('for_errors', __name__)


@basic_auth.error_handler
def basic_auth_error(status: int = 401) -> Response:
    error = (Forbidden if status == 403 else Unauthorized)()
    response = jsonify({
        'code': error.code,
        'message': error.name,
        'description': error.description,
    })
    response.status_code = error.code
    response.content_type = 'application/json'
    response.headers['WWW-Authenticate'] = 'Form'
    return response


@token_auth.error_handler
def token_auth_error(status: int = 401) -> Response:
    error = (Forbidden if status == 403 else Unauthorized)()
    response = jsonify({
        'code': error.code,
        'message': error.name,
        'description': error.description,
    })
    response.status_code = error.code
    response.content_type = 'application/json'
    response.headers['WWW-Authenticate'] = 'Form'
    return response


@for_errors.errorhandler(HTTPException)
def http_error(error: HTTPException) -> Response:
    response = jsonify({
        'code': error.code,
        'message': error.name,
        'description': error.description,
    })
    response.status_code = error.code  # type: ignore[assignment]
    response.content_type = 'application/json'
    return response


@for_errors.errorhandler(IntegrityError)
def integrity_error(error: IntegrityError) -> Response:
    response = jsonify({
        'code': 400,
        'message': 'Database integrity error',
        'description': str(error.orig),
    })
    response.status_code = 400
    response.content_type = 'application/json'
    return response


@for_errors.errorhandler(SQLAlchemyError)
def sqlalchemy_error(error: SQLAlchemyError) -> Response:
    if current_app.config['DEBUG'] is True:
        response = jsonify({
            'code': InternalServerError.code,
            'message': 'Database error',
            'description': str(error),
        })
    else:
        response = jsonify({
            'code': InternalServerError.code,
            'message': InternalServerError().name,
            'description': InternalServerError.description,
        })
    response.status_code = 500
    response.content_type = 'application/json'
    return response
