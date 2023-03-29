from flask import jsonify
from flask.wrappers import Response
import sqlalchemy as sa

from . import api
from ... import db
from ...models import SocialMedia, get_or_404


@api.route('/socials/')
def get_socials() -> Response:
    socials = db.session.scalars(sa.select(SocialMedia)).all()
    return jsonify({'socials': [social.to_json() for social in socials]})


@api.route('/socials/<social_id>')
def get_social(social_id: str) -> Response:
    social = get_or_404(SocialMedia, social_id)
    return jsonify(social.to_json())
