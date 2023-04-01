from uuid import UUID

from apifairy import authenticate, body, response, other_responses
from flask import Blueprint
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence

from ... import db, token_auth
from ...models import SocialMedia, User, get_or_404
from ...schemas import SocialMediaSchema
from ...utils import admin_required

for_socials = Blueprint('for_socials', __name__)

social_schema = SocialMediaSchema()
socials_schema = SocialMediaSchema(many=True)


@for_socials.route('/socials/', methods=['GET'])
@authenticate(token_auth)
@admin_required
@response(socials_schema)
def get_all() -> Sequence:
    """Retrieve all socials"""
    socials = db.session.scalars(sa.select(SocialMedia)).all()
    return socials  # type: ignore[return-value]


@for_socials.route('/socials/<uuid:social_id>', methods=['GET'])
@authenticate(token_auth)
@admin_required
@response(social_schema)
@other_responses({
    404: 'Not found',
    403: 'You are not allowed to perform this operation'
})
def get_one(social_id: UUID) -> SocialMedia:
    """Retrieve social page by id"""
    social = get_or_404(SocialMedia, social_id)
    return social


@for_socials.route('/socials/<uuid:social_id>', methods=['PUT'])
@authenticate(token_auth)
@admin_required
@body(social_schema)
@response(social_schema)
@other_responses({
    404: 'Not found',
    403: 'You are not allowed to perform this operation'
})
def update_one(kwargs: dict, social_id: UUID) -> SocialMedia:
    """Update social page"""
    social = get_or_404(SocialMedia, social_id)
    social.update(kwargs)
    db.session.commit()
    return social


@for_socials.route('/users/<uuid:user_id>/socials', methods=['GET'])
@authenticate(token_auth)
@admin_required
@response(social_schema)
@other_responses({
    404: 'User not found',
    403: 'You are not allowed to perform this operation'
})
def get_user_socials(user_id: UUID) -> SocialMedia:
    """Retrieve user's social page"""
    user = get_or_404(User, user_id)
    return user.socials


@for_socials.route('/users/<uuid:user_id>/socials', methods=['PUT'])
@authenticate(token_auth)
@admin_required
@body(social_schema)
@response(social_schema)
@other_responses({
    404: 'User not found',
    403: 'You are not allowed to perform this operation'
})
def update_user_socials(kwargs: dict, user_id: UUID) -> SocialMedia:
    """Update user's social page"""
    user = get_or_404(User, user_id)
    user.socials.update(kwargs)
    db.session.commit()
    return user.socials


@for_socials.route('/me/socials', methods=['GET'])
@authenticate(token_auth)
@response(social_schema)
def my_socials() -> SocialMedia:
    """Retrieve my socials"""
    user: User = token_auth.current_user()
    return user.socials  # type: ignore[return-value]


@for_socials.route('/me/socials', methods=['PUT'])
@authenticate(token_auth)
@body(social_schema)
@response(social_schema)
def update_my_socials(kwargs: dict) -> SocialMedia:
    """Update my socials"""
    user: User = token_auth.current_user()
    user.socials.update(kwargs)
    db.session.commit()
    return user.socials  # type: ignore[return-value]
