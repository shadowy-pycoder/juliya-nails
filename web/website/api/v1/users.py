from flask import jsonify
from flask.wrappers import Response
import sqlalchemy as sa

from . import api
from ... import db
from ...models import User, Post, Entry, get_or_404


@api.route('/users/')
def get_users() -> Response:
    users = db.session.scalars(sa.select(User)).all()
    return jsonify({'users': [user.to_json() for user in users]})


@api.route('/users/<user_id>')
def get_user(user_id: str) -> Response:
    user = get_or_404(User, user_id)
    return jsonify(user.to_json())


@api.route('/users/<user_id>/posts/')
def get_user_posts(user_id: str) -> Response:
    user = get_or_404(User, user_id)
    posts = db.session.scalars(user.posts.select().order_by(Post.posted_on.desc())).all()
    return jsonify({'posts': [post.to_json() for post in posts]})


@api.route('/users/<user_id>/socials/')
def get_user_socials(user_id: str) -> Response:
    user = get_or_404(User, user_id)
    return jsonify(user.socials.to_json())


@api.route('/users/<user_id>/entries/')
def get_user_entries(user_id: str) -> Response:
    user = get_or_404(User, user_id)
    entries = db.session.scalars(user.entries.select().order_by(Entry.date.desc(), Entry.time.desc())).all()
    return jsonify({'entries': [entry.to_json() for entry in entries]})
