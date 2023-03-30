from apifairy import authenticate, body, response, other_responses
from flask import jsonify
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence

from . import api
from . authentication import basic_auth
from ... import db
from ...models import Post, get_or_404
from ...schemas import PostSchema

post_schema = PostSchema()
posts_schema = PostSchema(many=True)


@api.route('/posts')
@response(posts_schema)
def get_posts() -> Sequence:
    posts = db.session.scalars(sa.select(Post).order_by(Post.posted_on.desc())).all()
    return posts  # type: ignore[return-value]


@api.route('/posts/<int:post_id>')
@response(post_schema)
@other_responses({404: 'Post not found'})
def get_post(post_id: int) -> Post:
    post = get_or_404(Post, post_id)
    return post
