from uuid import UUID

from apifairy import authenticate, body, response
from flask import jsonify, abort
from flask.wrappers import Response
import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import Sequence

from . import api
from ... import db
from ...models import User, Post, Entry, SocialMedia, get_or_404
from ...schemas import UserSchema

user_schema = UserSchema()
users_schema = UserSchema(many=True)


@api.route('/users', methods=['POST'])
@body(user_schema)
@response(user_schema, 201)
def create_user(kwargs: dict[str, str]) -> User:
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


@api.route('/users', methods=['GET'])
@response(users_schema)
def get_users() -> Sequence:
    """Get all users"""
    users = db.session.scalars(sa.select(User)).all()
    return users  # type: ignore[return-value]


@api.route('/users/<uuid:user_id>', methods=['GET'])
@response(user_schema)
def get_user(user_id: UUID) -> User:
    """Retrieve a user by uuid"""
    user = get_or_404(User, user_id)
    return user


@api.route('/users/<username>')
@response(user_schema)
def get_username(username: str) -> User:
    """Retrieve a user by username"""
    user = db.session.scalar(sa.select(User).filter_by(username=username)) or abort(404)
    return user


from .posts import posts_schema  # nopep8


@api.route('/users/<uuid:user_id>/posts')
@response(posts_schema)
def get_user_posts(user_id: UUID) -> Sequence:
    user = get_or_404(User, user_id)
    posts = db.session.scalars(user.posts.select().order_by(Post.posted_on.desc())).all()
    return posts  # type: ignore[return-value]


from .socials import social_schema  # nopep8


@api.route('/users/<uuid:user_id>/socials')
@response(social_schema)
def get_user_socials(user_id: UUID) -> SocialMedia:
    user = get_or_404(User, user_id)
    return user.socials


from .entries import entries_schema  # nopep8


@api.route('/users/<uuid:user_id>/entries')
@response(entries_schema)
def get_user_entries(user_id: UUID) -> Response:
    user = get_or_404(User, user_id)
    entries = db.session.scalars(user.entries.select().order_by(Entry.date.desc(), Entry.time.desc())).all()
    return entries  # type: ignore[return-value]
