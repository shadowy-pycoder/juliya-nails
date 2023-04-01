from uuid import UUID

from apifairy import authenticate, body, response, other_responses
from flask import abort, Blueprint
import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import Sequence

from ... import db, token_auth
from ...models import User, SocialMedia, get_or_404
from ...schemas import UserSchema, UpdateUserSchema, AdminUserSchema, EmptySchema
from ...utils import admin_required, delete_image

for_users = Blueprint('for_users', __name__)

user_schema = UserSchema()
users_schema = UserSchema(many=True)
update_user_schema = UpdateUserSchema(partial=True)
admin_user_schema = AdminUserSchema(partial=True)


@for_users.route('/users/', methods=['POST'])
@body(user_schema)
@response(user_schema, 201)
def create_one(kwargs: dict[str, str]) -> User:
    """Create a new user"""
    user = User(**kwargs)
    user.confirmed = True
    user.confirmed_on = func.now()
    db.session.add(user)
    db.session.commit()
    registered_user = db.session.scalar(sa.select(User).filter_by(username=user.username))
    if registered_user:
        socials = SocialMedia(user_id=registered_user.uuid)
        db.session.add(socials)
        db.session.commit()
    return user


@for_users.route('/users/', methods=['GET'])
@authenticate(token_auth)
@response(users_schema)
def get_all() -> Sequence:
    """Get all users"""
    users = db.session.scalars(sa.select(User)).all()
    return users  # type: ignore[return-value]


@for_users.route('/users/<uuid:user_id>', methods=['GET'])
@authenticate(token_auth)
@response(user_schema)
@other_responses({404: 'User not found'})
def get_one(user_id: UUID) -> User:
    """Retrieve user by uuid"""
    user = get_or_404(User, user_id)
    return user


@for_users.route('/users/<username>', methods=['GET'])
@authenticate(token_auth)
@response(user_schema)
@other_responses({404: 'User not found'})
def get_username(username: str) -> User:
    """Retrieve user by username"""
    user = db.session.scalar(sa.select(User).filter_by(username=username)) or abort(404)
    return user


@for_users.route('/users/<uuid:user_id>', methods=['PUT'])
@authenticate(token_auth)
@admin_required
@body(admin_user_schema)
@response(admin_user_schema, 201)
@other_responses({
    404: 'User not found',
    403: 'You are not allowed to perform this operation'
})
def update_one(kwargs: dict, user_id: UUID) -> User:
    """Update user"""
    user = get_or_404(User, user_id)
    user.update(kwargs)
    db.session.commit()
    return user


@for_users.route('/users/<uuid:user_id>', methods=['DELETE'])
@authenticate(token_auth)
@admin_required
@other_responses({
    404: 'User not found',
    403: 'You are not allowed to perform this operation'
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
def me() -> User:
    """Retrieve the authenticated user"""
    return token_auth.current_user()


@for_users.route('/me', methods=['PUT'])
@authenticate(token_auth)
@body(update_user_schema)
@response(user_schema)
@other_responses({400: 'Something wrong with password or email'})
def update_me(kwargs: dict[str, str]) -> User:
    """Update the authenticated user"""
    user: User = token_auth.current_user()
    if 'password' in kwargs and 'old_password' not in kwargs:
        abort(400, 'You must insert old password to create new one')
    elif 'old_password' in kwargs:
        abort(400, 'You must specify password to create or omit old password')
    user.update(kwargs)
    db.session.commit()
    return user
