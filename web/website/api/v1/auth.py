from apifairy import authenticate, response
import sqlalchemy as sa

from . import api
from ... import db, basic_auth, token_auth
from ...models import User, current_user
from ...schemas import TokenSchema


token_schema = TokenSchema()


@basic_auth.verify_password
def verify_password(username: str, password: str) -> User | None:
    if username and password:
        user = db.session.scalar(sa.select(User).filter_by(username=username))
        if not user:
            user = db.session.scalar(sa.select(User).filter_by(email=username))
        if user and user.verify_password(password):
            return user
    return None


@api.route('/get-auth-token', methods=['POST'])
@authenticate(basic_auth)
@response(token_schema)
def get_auth_token() -> dict:
    """Get auth token"""
    user: User = basic_auth.current_user()
    token = user.generate_token(context='auth', salt_context='auth-token')
    return dict(token=token)


@token_auth.verify_token
def verify_token(token: str | bytes) -> User | None:
    user = None
    if token:
        user = User.verify_token(token, context='auth', salt_context='auth-token')
    elif current_user.is_authenticated:
        user = current_user
    return user
