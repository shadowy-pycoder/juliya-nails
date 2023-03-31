from uuid import UUID

from apifairy import authenticate, body, response, other_responses
from flask import jsonify, Blueprint
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence

from ... import db, token_auth
from ...models import Post, User, get_or_404
from ...schemas import PostSchema

for_posts = Blueprint('for_posts', __name__)

post_schema = PostSchema()
posts_schema = PostSchema(many=True)


@for_posts.route('/posts/')
@authenticate(token_auth)
@response(posts_schema)
def get_all() -> Sequence:
    posts = db.session.scalars(sa.select(Post).order_by(Post.posted_on.desc())).all()
    return posts  # type: ignore[return-value]


@for_posts.route('/posts/<int:post_id>')
@authenticate(token_auth)
@response(post_schema)
@other_responses({404: 'Post not found'})
def get_one(post_id: int) -> Post:
    post = get_or_404(Post, post_id)
    return post


@for_posts.route('/users/<uuid:user_id>/posts')
@authenticate(token_auth)
@response(posts_schema)
def get_user_posts(user_id: UUID) -> Sequence:
    user = get_or_404(User, user_id)
    posts = db.session.scalars(user.posts.select().order_by(Post.posted_on.desc())).all()
    return posts  # type: ignore[return-value]


@for_posts.route('/me/posts', methods=['GET'])
@authenticate(token_auth)
@response(posts_schema)
def my_posts() -> Sequence:
    """Retrieve my posts"""
    user: User = token_auth.current_user()
    posts = db.session.scalars(user.posts.select().order_by(Post.posted_on.desc())).all()
    return posts  # type: ignore[return-value]
