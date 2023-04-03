from typing import Any
from uuid import UUID

from apifairy import authenticate, body, response, other_responses, arguments
from flask import Blueprint
from flask.wrappers import Response

from ..common import sanitize_query
from ... import db, token_auth
from ...models import SocialMedia, User, get_or_404
from ...schemas import (SocialMediaSchema, SocialsFieldSchema, SocialsFilterSchema, SocialsSortSchema,
                        NotFoundSchema, ForbiddenSchema)
from ...utils import admin_required

for_socials = Blueprint('for_socials', __name__)

social_schema = SocialMediaSchema()
socials_schema = SocialMediaSchema(many=True)


@for_socials.route('/socials', methods=['GET'])
@authenticate(token_auth)
@admin_required
@arguments(SocialsFieldSchema(only=['fields']))
@arguments(SocialsFilterSchema())
@arguments(SocialsSortSchema(only=['sort']))
@other_responses({
    200: socials_schema,
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def get_all(
        fields: dict[str, list[str]],
        filter: dict[str, Any],
        sort: dict[str, list[str]]) -> Response:
    """Retrieve all socials"""
    mapping = {'fields': SocialsFieldSchema, 'filter': SocialsFilterSchema, 'sort': SocialsSortSchema}
    socials, only = sanitize_query(fields=fields,
                                   filter=filter,
                                   sort=sort,
                                   obj=SocialMedia,
                                   model=SocialMedia,
                                   mapping=mapping)  # type: ignore[arg-type]
    return SocialMediaSchema(many=True, only=only).dump(socials)


@for_socials.route('/socials/<uuid:social_id>', methods=['GET'])
@authenticate(token_auth)
@admin_required
@response(social_schema)
@other_responses({
    404: (NotFoundSchema, 'Not found'),
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def get_one(social_id: UUID) -> Response:
    """Retrieve social page by id"""
    social = get_or_404(SocialMedia, social_id)
    return social


@for_socials.route('/socials/<uuid:social_id>', methods=['PUT'])
@authenticate(token_auth)
@admin_required
@body(social_schema)
@response(social_schema)
@other_responses({
    404: (NotFoundSchema, 'Not found'),
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def update_one(kwargs: dict, social_id: UUID) -> Response:
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
    404: (NotFoundSchema, 'Not found'),
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def get_user_socials(user_id: UUID) -> Response:
    """Retrieve user's social page"""
    user = get_or_404(User, user_id)
    return user.socials


@for_socials.route('/users/<uuid:user_id>/socials', methods=['PUT'])
@authenticate(token_auth)
@admin_required
@body(social_schema)
@response(social_schema)
@other_responses({
    404: (NotFoundSchema, 'Not found'),
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def update_user_socials(kwargs: dict, user_id: UUID) -> Response:
    """Update user's social page"""
    user = get_or_404(User, user_id)
    user.socials.update(kwargs)
    db.session.commit()
    return user.socials


@for_socials.route('/me/socials', methods=['GET'])
@authenticate(token_auth)
@response(social_schema)
def my_socials() -> Response:
    """Retrieve my socials"""
    user: User = token_auth.current_user()
    return user.socials  # type: ignore[return-value]


@for_socials.route('/me/socials', methods=['PUT'])
@authenticate(token_auth)
@body(social_schema)
@response(social_schema)
def update_my_socials(kwargs: dict) -> Response:
    """Update my socials"""
    user: User = token_auth.current_user()
    user.socials.update(kwargs)
    db.session.commit()
    return user.socials  # type: ignore[return-value]
