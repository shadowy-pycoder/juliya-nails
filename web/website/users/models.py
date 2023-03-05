import uuid

from flask import abort, current_app

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

    def generate_token(self,
                       context='confirm',
                       salt_context='confirm-email'):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps({context: str(self.uuid)}, salt=salt_context)

    def valid_token(self,
                    token,
                    context='confirm',
                    salt_context='confirm-email',
                    expiration=3600
                    ):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token,
                                    salt=salt_context,
                                    max_age=expiration
                                    )
        except:
            return False
        if data.get(context) != str(self.uuid):
            return False
        self.confirmed = True
        self.confirmed_on = func.now()
        db.session.add(self)
        return True


class MyModelView(ModelView):
    def is_accessible(self):
        if not current_user.is_anonymous and current_user.admin:
            return current_user.is_authenticated
        return abort(404)


admin.add_view(MyModelView(User, db.session))
