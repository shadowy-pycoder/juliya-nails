from uuid import UUID

from apifairy import authenticate, body, response, other_responses, arguments
from flask import Blueprint, url_for, jsonify
from flask.wrappers import Response

from ..common import sanitize_query
from ... import db, token_auth
from ...models import Post, User, get_or_404
from ...schemas import PostSchema, PostFieldSchema, PostSortSchema, NotFoundSchema, ForbiddenSchema
from ...utils import admin_required, delete_image

for_posts = Blueprint('for_posts', __name__)

post_schema = PostSchema()
posts_schema = PostSchema(many=True)


@for_posts.route('/posts', methods=['POST'])
@authenticate(token_auth)
@admin_required
@body(post_schema)
@other_responses({
    201: post_schema,
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def create_one(kwargs: dict[str, str]) -> Response:
    """Create post"""
    user = token_auth.current_user()
    post = Post(author=user, **kwargs)
    db.session.add(post)
    db.session.commit()
    response = jsonify(post_schema.dump(post))
    response.status_code = 201
    response.headers['Location'] = url_for('api.for_posts.get_one', post_id=post.id, _external=True)
    return response


@for_posts.route('/posts', methods=['GET'])
@authenticate(token_auth)
@arguments(PostFieldSchema(only=['fields']))
@arguments(PostSortSchema(only=['sort']))
@other_responses({200: posts_schema})
def get_all(fields: dict[str, list[str]],
            sort: dict[str, list[str]]) -> Response:
    """Get all posts"""
    mapping = {'fields': PostFieldSchema, 'sort': PostSortSchema}
    posts, only = sanitize_query(fields=fields,
                                 filter=None,
                                 sort=sort,
                                 obj=Post,
                                 model=Post,
                                 mapping=mapping)  # type: ignore[arg-type]
    return PostSchema(many=True, only=only).dump(posts)


@for_posts.route('/posts/<int:post_id>', methods=['GET'])
@authenticate(token_auth)
@response(post_schema)
@other_responses({404: (NotFoundSchema, 'Post not found')})
def get_one(post_id: int) -> Response:
    """Retrieve post by id"""
    post = get_or_404(Post, post_id)
    return post


@for_posts.route('/posts/<int:post_id>', methods=['PUT'])
@authenticate(token_auth)
@admin_required
@body(post_schema)
@response(post_schema)
@other_responses({
    404: (NotFoundSchema, 'Post not found'),
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def update_one(kwargs: dict, post_id: int) -> Response:
    """Update post"""
    post = get_or_404(Post, post_id)
    post.update(kwargs)
    db.session.commit()
    return post


@for_posts.route('/posts/<int:post_id>', methods=['DELETE'])
@authenticate(token_auth)
@admin_required
@other_responses({
    404: (NotFoundSchema, 'Post not found'),
    403: (ForbiddenSchema, 'You are not allowed to perform this operation')
})
def delete_one(post_id: int) -> tuple[str, int]:
    """Delete post"""
    post = get_or_404(Post, post_id)
    delete_image(post.image)
    db.session.delete(post)
    db.session.commit()
    return '', 204


@for_posts.route('/users/<uuid:user_id>/posts', methods=['GET'])
@authenticate(token_auth)
@arguments(PostFieldSchema(only=['fields']))
@arguments(PostSortSchema(only=['sort']))
@other_responses({
    200: posts_schema,
    404: (NotFoundSchema, 'User not found')
})
def get_user_posts(fields: dict[str, list[str]],
                   sort: dict[str, list[str]],
                   user_id: UUID) -> Response:
    """Retrieve user's posts"""
    user = get_or_404(User, user_id)
    mapping = {'fields': PostFieldSchema, 'sort': PostSortSchema}
    posts, only = sanitize_query(fields=fields,
                                 filter=None,
                                 sort=sort,
                                 obj=user.posts,
                                 model=Post,
                                 mapping=mapping)  # type: ignore[arg-type]
    return PostSchema(many=True, only=only).dump(posts)


@for_posts.route('/me/posts', methods=['GET'])
@authenticate(token_auth)
@arguments(PostFieldSchema(only=['fields']))
@arguments(PostSortSchema(only=['sort']))
@other_responses({200: posts_schema})
def my_posts(fields: dict[str, list[str]],
             sort: dict[str, list[str]]) -> Response:
    """Retrieve my posts"""
    user: User = token_auth.current_user()
    mapping = {'fields': PostFieldSchema, 'sort': PostSortSchema}
    posts, only = sanitize_query(fields=fields,
                                 filter=None,
                                 sort=sort,
                                 obj=user.posts,
                                 model=Post,
                                 mapping=mapping)  # type: ignore[arg-type]
    return PostSchema(many=True, only=only).dump(posts)
