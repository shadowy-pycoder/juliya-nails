from flask import Blueprint

api = Blueprint('api', __name__)

from . import auth, entries, errors, posts, services, socials, users  # nopep8
