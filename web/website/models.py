from datetime import datetime, date as date_, time as time_
from typing import Union
import uuid
from uuid import UUID as UUID_

from flask import abort, current_app
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm, BaseForm
from flask_login import UserMixin, current_user
from flask_wtf.file import FileAllowed, FileField
from itsdangerous import URLSafeTimedSerializer
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import scoped_session
from sqlalchemy.sql import func
from wtforms import StringField
from wtforms.validators import ValidationError

from . import db, bcrypt
from .utils import save_image, delete_image, current_user

current_user: 'User' = current_user

association_table = sa.Table('association_table', db.Model.metadata,
                             sa.Column('entry_id', UUID(as_uuid=True), sa.ForeignKey('entries.uuid')),
                             sa.Column('service_id', sa.Integer, sa.ForeignKey('services.id'))
                             )


class User(UserMixin, db.Model):  # type: ignore[name-defined]

    __tablename__ = 'users'

    uuid: so.Mapped[UUID_] = so.mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: so.Mapped[str] = so.mapped_column(sa.String(20), unique=True, nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True, nullable=False)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(60), nullable=False)
    registered_on: so.Mapped[datetime] = so.mapped_column(sa.DateTime(
        timezone=True), nullable=False, server_default=func.now())
    confirmed: so.Mapped[bool] = so.mapped_column(nullable=False, default=False)
    confirmed_on: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=True)
    admin: so.Mapped[bool] = so.mapped_column(nullable=False, default=False)
    entries: so.Mapped['Entry'] = so.relationship(back_populates='user', cascade="all, delete-orphan")
    posts: so.Mapped['Post'] = so.relationship(back_populates='author', cascade="all, delete-orphan")
    socials: so.Mapped['SocialMedia'] = so.relationship(back_populates='user', cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User('{self.username}', '{self.email}')"

    @property
    def password(self) -> None:
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, candidate: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(candidate).decode('UTF-8')

    def verify_password(self, candidate: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, candidate)

    def get_id(self) -> UUID_:
        return self.uuid

    def generate_token(
        self,
        context: str = 'confirm',
        salt_context: str = 'confirm-email'
    ) -> str | bytes:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps({context: str(self.uuid)}, salt=salt_context)

    def confirm_email_token(
        self,
        token: str | bytes,
        context: str = 'confirm',
        salt_context: str = 'confirm-email',
        expiration: int = 3600
    ) -> bool:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data: dict = serializer.loads(
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
        token: str | bytes,
        salt_context: str = 'reset-password',
        expiration: int = 3600
    ) -> Union['User', None]:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data: dict = serializer.loads(
                token,
                salt=salt_context,
                max_age=expiration
            )
        except:
            return None
        user = db.session.get(User, (data.get('reset')))
        return user


class SocialMedia(db.Model):  # type: ignore[name-defined]

    __tablename__ = 'socials'

    uuid: so.Mapped[UUID_] = so.mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: so.Mapped[UUID_] = so.mapped_column(UUID(as_uuid=True), sa.ForeignKey('users.uuid'), nullable=False)
    user: so.Mapped['User'] = so.relationship(back_populates='socials')
    avatar: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False, default='default.jpg')
    first_name: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)
    last_name: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)
    phone_number: so.Mapped[str] = so.mapped_column(sa.String(50), unique=True, nullable=True)
    viber: so.Mapped[str] = so.mapped_column(sa.String(50), unique=True, nullable=True)
    whatsapp: so.Mapped[str] = so.mapped_column(sa.String(50), unique=True, nullable=True)
    instagram: so.Mapped[str] = so.mapped_column(sa.String(255), unique=True, nullable=True)
    telegram: so.Mapped[str] = so.mapped_column(sa.String(255), unique=True, nullable=True)
    youtube: so.Mapped[str] = so.mapped_column(sa.String(255), unique=True, nullable=True)
    website: so.Mapped[str] = so.mapped_column(sa.String(255), unique=True, nullable=True)
    vk: so.Mapped[str] = so.mapped_column(sa.String(255), unique=True, nullable=True)
    about: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=True)

    def __repr__(self) -> str:
        items = {}
        for item in vars(self.__class__):
            if not item.startswith('_') and item not in ['uuid', 'user_id']:
                val = getattr(self, item)
                if val is not None:
                    items[item] = val
        return ', '.join(f'{item}: {val}' for item, val in items.items())


class Post(db.Model):  # type: ignore[name-defined]

    __tablename__ = 'posts'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)
    posted_on: so.Mapped[datetime] = so.mapped_column(sa.DateTime(timezone=True), nullable=False, default=func.now())
    image: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=True)
    content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    author_id: so.Mapped[UUID_] = so.mapped_column(UUID(as_uuid=True), sa.ForeignKey('users.uuid'), nullable=False)
    author: so.Mapped['User'] = so.relationship(back_populates='posts')

    def __repr__(self) -> str:
        return f'Post({self.id}, "{self.title}", {self.posted_on}, {self.author.username})'


class Entry(db.Model):  # type: ignore[name-defined]

    __tablename__ = 'entries'

    uuid: so.Mapped[UUID_] = so.mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    services: so.Mapped['Service'] = so.relationship(secondary=association_table, back_populates='entries')
    created_on: so.Mapped[datetime] = so.mapped_column(sa.DateTime(
        timezone=True), nullable=False, server_default=func.now())
    date: so.Mapped[date_] = so.mapped_column(sa.Date, nullable=False)
    time: so.Mapped[time_] = so.mapped_column(sa.Time(timezone=True), nullable=False)
    user_id: so.Mapped[UUID_] = so.mapped_column(UUID(as_uuid=True), sa.ForeignKey('users.uuid'), nullable=False)
    user: so.Mapped['User'] = so.relationship(back_populates='entries')

    def __repr__(self) -> str:
        return f'Entry({self.uuid}, {self.date}, {self.time}, {self.services}, {self.user.username})'


class Service(db.Model):  # type: ignore[name-defined]

    __tablename__ = 'services'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, nullable=False)
    duration: so.Mapped[float] = so.mapped_column(nullable=False)
    entries: so.Mapped['Entry'] = so.relationship(secondary=association_table, back_populates='services')

    def __repr__(self) -> str:
        return self.name


class AdminView(ModelView):
    column_display_pk = True
    column_display_all_relations = True
    column_hide_backrefs = False
    form_base_class = SecureForm

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.static_folder = 'static'

    def is_accessible(self) -> bool:
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

    def on_model_change(self, form: BaseForm, model: User, is_created: bool) -> None:
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

    def on_form_prefill(self, form: BaseForm, id: Post) -> None:
        self.img = form.image.data

    def on_model_change(self, form: BaseForm, model: Post, is_created: bool) -> None:
        if form.new_image.data is not None:
            if not is_created:
                delete_image(self.img)
            model.image = save_image(form.new_image)

    def on_model_delete(self, model: Post) -> None:
        self.img = model.image

    def after_model_delete(self, model: Post) -> None:
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

    def on_form_prefill(self, form: BaseForm, id: SocialMedia) -> None:
        self.img = form.avatar.data

    def on_model_change(self, form: BaseForm, model: SocialMedia, is_created: bool) -> None:
        if form.profile_image.data is not None:
            if not is_created:
                delete_image(self.img, path='profiles')
            model.avatar = save_image(form.profile_image, path='profiles')

    def on_model_delete(self, model: SocialMedia) -> None:
        self.img = model.avatar

    def after_model_delete(self, model: SocialMedia) -> None:
        delete_image(self.img, path='profiles')


def add_admin_views(session: scoped_session) -> None:
    from . import admin
    admin.add_view(UserView(User, session))
    admin.add_view(EntryView(Entry, session))
    admin.add_view(PostView(Post, session))
    admin.add_view(ServiceView(Service, session))
    admin.add_view(SocialMediaView(SocialMedia, session))
