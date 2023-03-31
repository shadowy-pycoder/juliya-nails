from uuid import UUID

from apifairy import authenticate, body, response
from flask import jsonify, abort
from flask.wrappers import Response
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence

from . import api
from ... import db, token_auth
from ...models import SocialMedia, User, get_or_404
from ...schemas import SocialMediaSchema

social_schema = SocialMediaSchema()
socials_schema = SocialMediaSchema(many=True)


@api.route('/socials/', methods=['GET'])
@authenticate(token_auth)
@response(socials_schema)
def get_socials() -> Sequence:
    """Retrieve all socials"""
    socials = db.session.scalars(sa.select(SocialMedia)).all()
    return socials  # type: ignore[return-value]


@api.route('/socials/<uuid:social_id>', methods=['GET'])
@authenticate(token_auth)
@response(social_schema)
def get_social(social_id: UUID) -> SocialMedia:
    """Retrieve user's social page"""
    social = get_or_404(SocialMedia, social_id)
    return social


@api.route('/users/<uuid:user_id>/socials')
@authenticate(token_auth)
@response(social_schema)
def get_user_socials(user_id: UUID) -> SocialMedia:
    user = get_or_404(User, user_id)
    return user.socials


@api.route('/socials/<uuid:social_id>', methods=['PUT'])
@authenticate(token_auth)
@body(social_schema)
@response(social_schema)
def update_social(kwargs: dict, social_id: UUID) -> SocialMedia:
    """Update social page"""
    social = get_or_404(SocialMedia, social_id)
    if social.user != token_auth.current_user():
        abort(403)
    social.update(kwargs)
    db.session.commit()
    return social


@api.route('/me/socials', methods=['GET'])
@authenticate(token_auth)
@response(social_schema)
def my_socials() -> SocialMedia:
    """Retrieve my socials"""
    user: User = token_auth.current_user()
    return user.socials  # type: ignore[return-value]


@api.route('/me/socials', methods=['PUT'])
@authenticate(token_auth)
@body(social_schema)
@response(social_schema)
def update_my_socials(kwargs: dict) -> SocialMedia:
    """Update my socials"""
    user: User = token_auth.current_user()
    user.socials.update(kwargs)
    db.session.commit()
    return user.socials  # type: ignore[return-value]
