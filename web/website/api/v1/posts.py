from flask import jsonify
from flask.wrappers import Response
import sqlalchemy as sa

from . import api
from ... import db
from ...models import Post, get_or_404


@api.route('/posts/')
def get_posts() -> Response:
    posts = db.session.scalars(sa.select(Post).order_by(Post.posted_on.desc())).all()
    return jsonify({'posts': [post.to_json() for post in posts]})


@api.route('/posts/<int:post_id>')
def get_post(post_id: int) -> Response:
    post = get_or_404(Post, post_id)
    return jsonify(post.to_json())
