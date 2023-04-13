from typing import Any
from uuid import UUID

from apifairy import authenticate, body, response, other_responses, arguments
from flask import Blueprint, current_app
from flask.wrappers import Response

from ..common import sanitize_query
from ... import db, token_auth
from ...models import SocialMedia, User, get_or_404
from ...schemas import (SocialMediaSchema, SocialsFieldSchema, SocialsFilterSchema, SocialsSortSchema,
                        NotFoundSchema, ForbiddenSchema, PaginationSchema, PaginatedSchema, UserAvatarSchema)
from ...utils import admin_required, delete_image

for_socials = Blueprint('for_socials', __name__)

social_schema = SocialMediaSchema()
avatar_schema = UserAvatarSchema()
socials_schema = PaginatedSchema(SocialMediaSchema(many=True))


@for_socials.route('/socials', methods=['GET'])
@authenticate(token_auth)
@admin_required
@arguments(SocialsFieldSchema(only=['fields']))
@arguments(SocialsFilterSchema())
@arguments(SocialsSortSchema(only=['sort']))
@arguments(PaginationSchema())
@other_responses({
    200: socials_schema,
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def get_all(
        fields: dict[str, list[str]],
        filter: dict[str, Any],
        sort: dict[str, list[str]],
        pagination: dict[str, int]) -> Response:
    """Retrieve all socials"""
    mapping = {'fields': SocialsFieldSchema, 'filter': SocialsFilterSchema, 'sort': SocialsSortSchema}
    socials, only, pagination = sanitize_query(fields=fields,
                                               filter=filter,
                                               sort=sort,
                                               pagination=pagination,
                                               obj=SocialMedia,
                                               model=SocialMedia,
                                               mapping=mapping)  # type: ignore[arg-type]
    return PaginatedSchema(SocialMediaSchema(many=True, only=only))().dump({'results': socials,
                                                                            'pagination': pagination})


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


@for_socials.route('/users/<uuid:user_id>/socials/avatar', methods=['PUT'])
@authenticate(token_auth)
@admin_required
@body(avatar_schema, location='form')
@response(social_schema)
@other_responses({
    404: (NotFoundSchema, 'Not found'),
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def update_user_avatar(kwargs: dict, user_id: UUID) -> Response:
    """Update user's avatar"""
    user = get_or_404(User, user_id)
    user.socials.avatar = kwargs['avatar']
    db.session.commit()
    return user.socials


@for_socials.route('/users/<uuid:user_id>/socials/avatar', methods=['DELETE'])
@authenticate(token_auth)
@admin_required
@other_responses({
    404: (NotFoundSchema, 'Not found'),
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def delete_user_avatar(user_id: UUID) -> tuple[str, int]:
    """Delete user's avatar"""
    user = get_or_404(User, user_id)
    delete_image(user.socials.avatar, path='profiles')
    user.socials.avatar = current_app.config['DEFAULT_AVATAR']
    db.session.commit()
    return '', 204


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


@for_socials.route('/me/socials/avatar', methods=['PUT'])
@authenticate(token_auth)
@body(avatar_schema, location='form')
@response(social_schema)
def update_my_avatar(kwargs: dict) -> Response:
    """Update my avatar"""
    user: User = token_auth.current_user()
    user.socials.avatar = kwargs['avatar']
    db.session.commit()
    return user.socials  # type: ignore[return-value]


@for_socials.route('/me/socials/avatar', methods=['DELETE'])
@authenticate(token_auth)
def delete_my_avatar() -> tuple[str, int]:
    """Delete my avatar"""
    user: User = token_auth.current_user()
    delete_image(user.socials.avatar, path='profiles')
    user.socials.avatar = current_app.config['DEFAULT_AVATAR']
    db.session.commit()
    return '', 204
