from flask import Blueprint

api = Blueprint('api', __name__)

from . import authentication, entries, errors, posts, services, socials, users  # nopep8
