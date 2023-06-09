from typing import Any, Annotated
from uuid import UUID

from apifairy import authenticate, arguments, body, response, other_responses
from flask import abort, Blueprint, jsonify, url_for
from flask.wrappers import Response
import sqlalchemy as sa

from ..common import sanitize_query
from ... import db, token_auth
from ...models import User, SocialMedia, get_or_404
from ...schemas import (UserSchema, UpdateUserSchema, AdminUserSchema, UserFieldSchema,
                        UserSortSchema, UserFilterSchema, NotFoundSchema, ForbiddenSchema,
                        PaginationSchema, PaginatedSchema)
from ...utils import admin_required, delete_image

for_users = Blueprint('for_users', __name__)

user_schema = UserSchema()
users_schema = PaginatedSchema(UserSchema(many=True))
update_user_schema = UpdateUserSchema(partial=True)
admin_user_schema = AdminUserSchema(partial=True)


@for_users.route('/users', methods=['POST'])
@body(user_schema)
@other_responses({201: user_schema})
def create_one(kwargs: dict[str, str]) -> Response:
    """Create a new user"""
    user = User(**kwargs)
    db.session.add(user)
    db.session.commit()
    registered_user = db.session.scalar(sa.select(User).filter_by(username=user.username))
    if registered_user:
        socials = SocialMedia(user_id=registered_user.uuid)
        db.session.add(socials)
        db.session.commit()
    response = jsonify(user_schema.dump(user))
    response.status_code = 201
    response.headers['Location'] = url_for('api.for_users.get_one', user_id=user.uuid, _external=True)
    return response


@for_users.route('/users', methods=['GET'])
@authenticate(token_auth)
@arguments(UserFieldSchema(only=['fields']))
@arguments(UserFilterSchema())
@arguments(UserSortSchema(only=['sort']))
@arguments(PaginationSchema())
@other_responses({200: users_schema})
def get_all(fields: dict[str, list[str]],
            filter: dict[str, Any],
            sort: dict[str, list[str]],
            pagination: dict[str, int]) -> Response:
    """Get all users"""
    mapping = {'fields': UserFieldSchema, 'filter': UserFilterSchema, 'sort': UserSortSchema}
    users, only, pagination = sanitize_query(fields=fields,
                                             filter=filter,
                                             sort=sort,
                                             pagination=pagination,
                                             obj=User,
                                             model=User,
                                             mapping=mapping)  # type: ignore[arg-type]
    return PaginatedSchema(UserSchema(many=True, only=only))().dump({'results': users,
                                                                    'pagination': pagination})


@for_users.route('/users/<uuid:user_id>', methods=['GET'])
@authenticate(token_auth)
@response(user_schema)
@other_responses({404: (NotFoundSchema, 'User not found')})
def get_one(user_id: Annotated[UUID, 'UUID of the user to retrieve']) -> Response:
    """Retrieve user by uuid"""
    user = get_or_404(User, user_id)
    return user


@for_users.route('/users/<uuid:user_id>', methods=['PUT'])
@authenticate(token_auth)
@admin_required
@body(admin_user_schema)
@response(admin_user_schema)
@other_responses({
    404: (NotFoundSchema, 'User not found'),
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def update_one(kwargs: dict, user_id: UUID) -> Response:
    """Update user"""
    user = get_or_404(User, user_id)
    user.update(kwargs)
    db.session.commit()
    return user


@for_users.route('/users/<uuid:user_id>', methods=['DELETE'])
@authenticate(token_auth)
@admin_required
@other_responses({
    404: (NotFoundSchema, 'User not found'),
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def delete_one(user_id: UUID) -> tuple[str, int]:
    """Delete user"""
    user = get_or_404(User, user_id)
    if user.admin:
        abort(403, 'Attempt to delete admin user')
    delete_image(user.socials.avatar, path='profiles')
    db.session.delete(user)
    db.session.commit()
    return '', 204


@for_users.route('/me', methods=['GET'])
@authenticate(token_auth)
@response(user_schema)
def me() -> Response:
    """Retrieve the authenticated user"""
    return token_auth.current_user()


@for_users.route('/me', methods=['PUT'])
@authenticate(token_auth)
@body(update_user_schema)
@response(user_schema)
@other_responses({400: 'Something wrong with password or email'})
def update_me(kwargs: dict[str, str]) -> Response:
    """Update the authenticated user"""
    user: User = token_auth.current_user()
    user.update(kwargs)
    db.session.commit()
    return user
