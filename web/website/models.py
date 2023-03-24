import uuid

from flask import abort, current_app
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_login import UserMixin, current_user
from flask_wtf.file import FileAllowed, FileField
from itsdangerous import URLSafeTimedSerializer
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects.postgresql import UUID, FLOAT
from sqlalchemy.sql import func
from wtforms import StringField
from wtforms.validators import ValidationError

from . import db, bcrypt
from .utils import save_image, delete_image


Base = db.base


association_table = sa.Table('association_table', Base.metadata,
                             sa.Column('entry_id', UUID(as_uuid=True), sa.ForeignKey('entries.uuid')),
                             sa.Column('service_id', sa.Integer, sa.ForeignKey('services.id'))
                             )


class User(UserMixin, Base):

    __tablename__ = 'users'

    uuid = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = sa.Column(sa.String(20), unique=True, nullable=False)
    email = sa.Column(sa.String(100), unique=True, nullable=False)
    password_hash = sa.Column(sa.String(60), nullable=False)
    registered_on = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    confirmed = sa.Column(sa.Boolean, nullable=False, default=False)
    confirmed_on = sa.Column(sa.DateTime(timezone=True), nullable=True)
    admin = sa.Column(sa.Boolean, nullable=False, default=False)
    entries = so.relationship('Entry', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")
    posts = so.relationship('Post', back_populates='author', lazy='dynamic', cascade="all, delete-orphan")
    socials = so.relationship('SocialMedia', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

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


class SocialMedia(Base):

    __tablename__ = 'socials'

    uuid = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('users.uuid'), nullable=False)
    user = so.relationship('User', back_populates='socials')
    avatar = sa.Column(sa.String(20), nullable=False, default='default.jpg')
    first_name = sa.Column(sa.String(50), nullable=True)
    last_name = sa.Column(sa.String(50), nullable=True)
    phone_number = sa.Column(sa.String(50), unique=True, nullable=True)
    viber = sa.Column(sa.String(50), unique=True, nullable=True)
    whatsapp = sa.Column(sa.String(50), unique=True, nullable=True)
    instagram = sa.Column(sa.String(255), unique=True, nullable=True)
    telegram = sa.Column(sa.String(255), unique=True, nullable=True)
    youtube = sa.Column(sa.String(255), unique=True, nullable=True)
    website = sa.Column(sa.String(255), unique=True, nullable=True)
    vk = sa.Column(sa.String(255), unique=True)
    about = sa.Column(sa.String(255), nullable=True)

    def __repr__(self):
        items = {}
        for item in vars(__class__):
            if not item.startswith('_') and item not in ['uuid', 'user_id']:
                val = getattr(self, item)
                if val is not None:
                    items[item] = val
        return ', '.join(f'{item}: {val}' for item, val in items.items())


class Post(Base):

    __tablename__ = 'posts'

    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.String(100), nullable=False)
    posted_on = sa.Column(sa.DateTime, nullable=False, default=func.now())
    image = sa.Column(sa.String(20))
    content = sa.Column(sa.Text, nullable=False)
    author_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('users.uuid'), nullable=False)
    author = so.relationship('User', back_populates='posts')

    def __repr__(self):
        return f'Post({self.id}, "{self.title}", {self.posted_on}, {self.author.username})'


class Entry(Base):

    __tablename__ = 'entries'

    uuid = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    services = so.relationship('Service', secondary=association_table, back_populates='entries')
    created_on = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=func.now())
    date = sa.Column(sa.Date, nullable=False)
    time = sa.Column(sa.Time(timezone=True), nullable=False)
    user_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('users.uuid'), nullable=False)
    user = so.relationship('User', back_populates='entries')

    def __repr__(self):
        return f'Entry({self.uuid}, {self.date}, {self.time}, {self.services}, {self.user.username})'


class Service(Base):

    __tablename__ = 'services'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(64), unique=True, nullable=False)
    duration = sa.Column(FLOAT(), nullable=False)
    entries = so.relationship('Entry', secondary=association_table, back_populates='services', lazy='dynamic')

    def __repr__(self):
        return self.name


class AdminView(ModelView):
    column_display_pk = True
    column_display_all_relations = True
    column_hide_backrefs = False
    form_base_class = SecureForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.static_folder = 'static'

    def is_accessible(self):
        if not current_user.is_anonymous and current_user.admin:
            return current_user.is_authenticated
        return abort(404)


class UserView(AdminView):
    column_list = ('uuid',
                   'username',
                   'email',
                   'password_hash',
                   'confirmed',
                   'confirmed_on',
                   'admin',
                   )
    column_searchable_list = ('username', 'email')
    column_default_sort = ('admin', True)

    form_excluded_columns = ('password_hash')

    form_extra_fields = {
        'new_password': StringField('New Password'),
    }

    form_columns = (
        'username',
        'email',
        'new_password',
        'confirmed',
        'confirmed_on',
        'admin',
        'entries',
        'posts',
        'socials',
    )

    def on_model_change(self, form, model: User, is_created):
        if form.new_password.data != '':
            model.password = form.new_password.data
        elif is_created and form.new_password.data == '':
            raise ValidationError('Password must not be empty.')


class PostView(AdminView):
    column_list = ('id', 'title', 'posted_on', 'image', 'content', 'author_id', 'author.username')
    column_searchable_list = ('author.username', 'content',)
    column_default_sort = ('posted_on', True)

    form_extra_fields = {
        'new_image': FileField('Upload Post Image', validators=[FileAllowed(['jpg', 'png'])]),
    }

    form_columns = (
        'title',
        'posted_on',
        'image',
        'new_image',
        'content',
        'author_id',
        'author',

    )
    form_widget_args = {
        'image': {
            'disabled': True
        }
    }

    def on_form_prefill(self, form, id):
        self.img = form.image.data

    def on_model_change(self, form, model: Post, is_created):
        if form.new_image.data is not None:
            if not is_created:
                delete_image(self.img)
            model.image = save_image(form.new_image)

    def on_model_delete(self, model: Post):
        self.img = model.image

    def after_model_delete(self, model: Post):
        delete_image(self.img)


class ServiceView(AdminView):
    column_list = ('id', 'name', 'duration',)
    column_editable_list = ('name', 'duration')


class EntryView(AdminView):
    column_list = ('uuid', 'created_on', 'date', 'time', 'user_id', 'user.username', 'services')
    column_searchable_list = ('user.username',)
    column_default_sort = ('date', True)


class SocialMediaView(AdminView):
    column_searchable_list = ('phone_number',)
    column_default_sort = ('phone_number', True)
    column_editable_list = (
        'first_name',
        'last_name',
        'phone_number',
        'viber',
        'whatsapp',
        'instagram',
        'telegram',
        'youtube',
        'website',
        'vk',
        'about',
    )

    form_extra_fields = {
        'profile_image': FileField('Upload Profile Image', validators=[FileAllowed(['jpg', 'png'])]),
    }

    form_columns = (
        'user',
        'avatar',
        'profile_image',
        'first_name',
        'last_name',
        'phone_number',
        'viber',
        'whatsapp',
        'instagram',
        'telegram',
        'youtube',
        'website',
        'vk',
        'about',
    )

    form_widget_args = {
        'avatar': {
            'disabled': True
        }
    }

    def on_form_prefill(self, form, id):
        self.img = form.avatar.data

    def on_model_change(self, form, model: SocialMedia, is_created):
        if form.profile_image.data is not None:
            if not is_created:
                delete_image(self.img, path='profiles')
            model.avatar = save_image(form.profile_image, path='profiles')

    def on_model_delete(self, model: SocialMedia):
        self.img = model.avatar

    def after_model_delete(self, model: SocialMedia):
        delete_image(self.img, path='profiles')


def add_admin_views(session):
    from . import admin
    admin.add_view(UserView(User, session))
    admin.add_view(EntryView(Entry, session))
    admin.add_view(PostView(Post, session))
    admin.add_view(ServiceView(Service, session))
    admin.add_view(SocialMediaView(SocialMedia, session))


# class User(UserMixin, Base):

#     __tablename__ = 'users'

#     uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     username = db.Column(db.String(20), unique=True, nullable=False)
#     email = db.Column(db.String(100), unique=True, nullable=False)
#     password_hash = db.Column(db.String(60), nullable=False)
#     registered_on = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
#     confirmed = db.Column(db.Boolean, nullable=False, default=False)
#     confirmed_on = db.Column(db.DateTime(timezone=True), nullable=True)
#     admin = db.Column(db.Boolean, nullable=False, default=False)
#     entries = db.relationship('Entry', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")
#     posts = db.relationship('Post', back_populates='author', lazy='dynamic', cascade="all, delete-orphan")
#     socials = db.relationship('SocialMedia', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")

#     def __repr__(self):
#         return f"User('{self.username}', '{self.email}')"

#     @property
#     def password(self):
#         raise AttributeError('Password is not a readable attribute')

#     @password.setter
#     def password(self, candidate):
#         self.password_hash = bcrypt.generate_password_hash(candidate).decode('UTF-8')

#     def verify_password(self, candidate):
#         return bcrypt.check_password_hash(self.password_hash, candidate)

#     def get_id(self):
#         return self.uuid

#     def generate_token(
#         self,
#         context='confirm',
#         salt_context='confirm-email'
#     ):
#         serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
#         return serializer.dumps({context: str(self.uuid)}, salt=salt_context)

#     def confirm_email_token(
#         self,
#         token,
#         context='confirm',
#         salt_context='confirm-email',
#         expiration=3600
#     ):
#         serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
#         try:
#             data = serializer.loads(
#                 token,
#                 salt=salt_context,
#                 max_age=expiration
#             )
#         except:
#             return False
#         if data.get(context) != str(self.uuid):
#             return False
#         self.confirmed = True
#         self.confirmed_on = func.now()
#         return True

#     @staticmethod
#     def reset_password_token(
#         token,
#         salt_context='reset-password',
#         expiration=3600
#     ):
#         serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
#         try:
#             data = serializer.loads(
#                 token,
#                 salt=salt_context,
#                 max_age=expiration
#             )
#         except:
#             return False
#         user = User.query.get(data.get('reset'))
#         if user is None:
#             return False
#         return user


# class SocialMedia(db.Model):

#     __tablename__ = 'socials'

#     uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.uuid'), nullable=False)
#     user = db.relationship('User', back_populates='socials', lazy='select')
#     avatar = db.Column(db.String(20), nullable=False, default='default.jpg')
#     first_name = db.Column(db.String(50), nullable=True)
#     last_name = db.Column(db.String(50), nullable=True)
#     phone_number = db.Column(db.String(50), unique=True, nullable=True)
#     viber = db.Column(db.String(50), unique=True, nullable=True)
#     whatsapp = db.Column(db.String(50), unique=True, nullable=True)
#     instagram = db.Column(db.String(255), unique=True, nullable=True)
#     telegram = db.Column(db.String(255), unique=True, nullable=True)
#     youtube = db.Column(db.String(255), unique=True, nullable=True)
#     website = db.Column(db.String(255), unique=True, nullable=True)
#     vk = db.Column(db.String(255), unique=True)
#     about = db.Column(db.String(255), nullable=True)

#     def __repr__(self):
#         items = {}
#         for item in vars(__class__):
#             if not item.startswith('_') and item not in ['uuid', 'user_id']:
#                 val = getattr(self, item)
#                 if val is not None:
#                     items[item] = val
#         return ', '.join(f'{item}: {val}' for item, val in items.items())


# class Post(db.Model):

#     __tablename__ = 'posts'

#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     posted_on = db.Column(db.DateTime, nullable=False, default=func.now())
#     image = db.Column(db.String(20))
#     content = db.Column(db.Text, nullable=False)
#     author_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.uuid'), nullable=False)
#     author = db.relationship('User', back_populates='posts', lazy='select')

#     def __repr__(self):
#         return f'Post({self.id}, "{self.title}", {self.posted_on}, {self.author.username})'


# class Entry(db.Model):

#     __tablename__ = 'entries'

#     uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     services = db.relationship('Service', secondary=association_table, back_populates='entries', lazy='select')
#     created_on = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
#     date = db.Column(db.Date, nullable=False)
#     time = db.Column(db.Time(timezone=True), nullable=False)
#     user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.uuid'), nullable=False)
#     user = db.relationship('User', back_populates='entries', lazy='select')

#     def __repr__(self):
#         return f'Entry({self.uuid}, {self.date}, {self.time}, {self.services}, {self.user.username})'


# class Service(db.Model):

#     __tablename__ = 'services'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64), unique=True, nullable=False)
#     duration = db.Column(FLOAT(), nullable=False)
#     entries = db.relationship('Entry', secondary=association_table, back_populates='services', lazy='dynamic')

#     def __repr__(self):
#         return self.name
