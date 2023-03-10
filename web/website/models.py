import uuid

from flask import abort, current_app

from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin, current_user
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from . import db, login_manager, admin, bcrypt


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(UserMixin, db.Model):

    __tablename__ = 'users'

    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    registered_on = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime(timezone=True), nullable=True)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    entries = db.relationship('Entry', backref='user', lazy='dynamic')
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}', '{self.registered_on})"
    
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, candidate):
        self.password_hash = bcrypt.generate_password_hash(candidate).decode('UTF-8')

    def verify_password(self, candidate):
        return bcrypt.check_password_hash(self.password_hash, candidate)

    def get_id(self):
        return self.uuid

    def generate_token(
        self,
        context='confirm',
        salt_context='confirm-email'
    ):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps({context: str(self.uuid)}, salt=salt_context)

    def confirm_email_token(
        self,
        token,
        context='confirm',
        salt_context='confirm-email',
        expiration=3600
    ):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(
                token,
                salt=salt_context,
                max_age=expiration
            )
        except:
            return False
        if data.get(context) != str(self.uuid):
            return False
        self.confirmed = True
        self.confirmed_on = func.now()
        return True

    @staticmethod
    def reset_password_token(
        token,
        salt_context='reset-password',
        expiration=3600
    ):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(
                token,
                salt=salt_context,
                max_age=expiration
            )
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        return user
    

class Entry(db.Model):

    __tablename__ = 'entries'

    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(50), nullable=False)
    created_on = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    date_and_time = db.Column(db.DateTime(timezone=True), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.uuid'), nullable=False)

class Service(db.Model):

    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)


class Post(db.Model):

    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    posted_on = db.Column(db.DateTime, nullable=False, default=func.now())
    image = db.Column(db.String(20))
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.uuid'), nullable=False)

    


class MyModelView(ModelView):
    def is_accessible(self):
        if not current_user.is_anonymous and current_user.admin:
            return current_user.is_authenticated
        return abort(404)
    



admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Entry, db.session))
admin.add_view(MyModelView(Post, db.session))
