from uuid import UUID

from apifairy import authenticate, body, response, other_responses
from flask import Blueprint
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence

from ... import db, token_auth
from ...models import Post, User, get_or_404
from ...schemas import PostSchema
from ...utils import admin_required, delete_image

for_posts = Blueprint('for_posts', __name__)

post_schema = PostSchema()
posts_schema = PostSchema(many=True)


@for_posts.route('/posts/', methods=['POST'])
@authenticate(token_auth)
@admin_required
@body(post_schema)
@response(post_schema, 201)
@other_responses({
    403: 'You are not allowed to perform this operation'
})
def create_one(kwargs: dict[str, str]) -> Post:
    """Create post"""
    user = token_auth.current_user()
    post = Post(author=user, **kwargs)
    db.session.add(post)
    db.session.commit()
    return post


@for_posts.route('/posts/', methods=['GET'])
@authenticate(token_auth)
@response(posts_schema)
def get_all() -> Sequence:
    """Get all posts"""
    posts = db.session.scalars(sa.select(Post).order_by(Post.posted_on.desc())).all()
    return posts  # type: ignore[return-value]


@for_posts.route('/posts/<int:post_id>', methods=['GET'])
@authenticate(token_auth)
@response(post_schema)
@other_responses({404: 'Post not found'})
def get_one(post_id: int) -> Post:
    """Retrieve post by id"""
    post = get_or_404(Post, post_id)
    return post


@for_posts.route('/posts/<int:post_id>', methods=['PUT'])
@authenticate(token_auth)
@admin_required
@body(post_schema)
@response(post_schema)
@other_responses({
    404: 'Post not found',
    403: 'You are not allowed to perform this operation'
})
def update_one(kwargs: dict, post_id: int) -> Post:
    """Update post"""
    post = get_or_404(Post, post_id)
    post.update(kwargs)
    db.session.commit()
    return post


@for_posts.route('/posts/<int:post_id>', methods=['DELETE'])
@authenticate(token_auth)
@admin_required
@other_responses({
    404: 'Post not found',
    403: 'You are not allowed to perform this operation'
})
def delete_one(post_id: int) -> tuple[str, int]:
    """Delete post"""
    post = get_or_404(Post, post_id)
    delete_image(post.image)
    db.session.delete(post)
    db.session.commit()
    return '', 204


@for_posts.route('/users/<uuid:user_id>/posts')
@authenticate(token_auth)
@response(posts_schema)
@other_responses({404: 'User not found'})
def get_user_posts(user_id: UUID) -> Sequence:
    """Retrieve user's posts"""
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
