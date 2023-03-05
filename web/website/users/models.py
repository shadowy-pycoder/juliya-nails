import uuid

from flask import abort, flash, current_app

from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin, current_user
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from website import db, login_manager, admin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model, UserMixin):

    __tablename__ = 'user'

    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    registered_on = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime(timezone=True), nullable=True)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}', '{self.registered_on})"

    def get_id(self):
        return self.uuid

    def generate_confirmation_token(self):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.email, salt='confirm-email')

    @staticmethod
    def confirm_token(token, expiration=3600):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt='confirm-email',
                max_age=expiration
            )
        except:
            return False
        return email


class MyModelView(ModelView):
    pass
    # def is_accessible(self):
    #     if not current_user.is_anonymous and current_user.admin:
    #         flash(current_user)
    #         return current_user.is_authenticated
    #     return abort(404)


admin.add_view(MyModelView(User, db.session))
