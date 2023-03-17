import uuid

from flask import abort, current_app
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin, current_user
from flask_wtf.file import FileAllowed, FileField
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.dialects.postgresql import UUID, FLOAT
from sqlalchemy.sql import func
from wtforms import StringField
from wtforms.validators import ValidationError, DataRequired

from . import db, login_manager, admin, bcrypt
from .utils import save_image, delete_image


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


registrations = db.Table('registrations',
                         db.Column('entry_id', UUID(as_uuid=True), db.ForeignKey('entries.uuid')),
                         db.Column('service_id', db.Integer, db.ForeignKey('services.id'))
                         )


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
    appointment = db.relationship('Service', secondary=registrations,
                                  backref=db.backref('entries', lazy='dynamic'), lazy='dynamic')
    created_on = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time(timezone=True), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.uuid'), nullable=False)


class Service(db.Model):

    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    duration = db.Column(FLOAT(), nullable=False)

    def __repr__(self):
        return self.name


class Post(db.Model):

    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    posted_on = db.Column(db.DateTime, nullable=False, default=func.now())
    image = db.Column(db.String(20))
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.uuid'), nullable=False)


class MyModelView(ModelView):
    def is_accessible(self):
        if not current_user.is_anonymous and current_user.admin:
            return current_user.is_authenticated
        return abort(404)


class UserView(MyModelView):
    column_display_pk = True
    column_display_all_relations = True
    column_hide_backrefs = False
    form_excluded_columns = ('password_hash')
    column_list = ('uuid',
                   'username',
                   'email',
                   'password_hash',
                   'image_file',
                   'confirmed',
                   'confirmed_on',
                   'admin',
                   'posts2')

    form_extra_fields = {
        'new_password': StringField('New Password'),
        'profile_image': FileField('Upload Profile Image', validators=[FileAllowed(['jpg', 'png'])]),
        'uuid': StringField('User UUID', validators=[DataRequired()]),
        'posts': StringField('User posts')
    }

    form_columns = (
        'uuid',
        'username',
        'email',
        'new_password',
        'image_file',
        'profile_image',
        'confirmed',
        'confirmed_on',
        'admin',
        'posts',
    )
    form_widget_args = {
        'image_file': {
            'disabled': True
        }
    }

    def on_form_prefill(self, form, id):
        self.img = form.image_file.data
        form.posts.data = self.model.query.get(id).posts.all()

    def on_model_change(self, form, model: User, is_created):
        if form.new_password.data != '':
            model.password = form.new_password.data
        elif is_created:
            raise ValidationError('Password must not be empty.')

        if form.profile_image.data is not None:
            if not is_created and self.img != 'default.jpg':
                try:
                    delete_image(self.img, path='profiles')
                except FileNotFoundError:
                    pass
            model.image_file = save_image(form.profile_image, path='profiles')

    def on_model_delete(self, model: User):
        self.img = model.image_file

    def after_model_delete(self, model: User):
        if self.img != 'default.jpg':
            try:
                delete_image(self.img, path='profiles')
            except FileNotFoundError:
                pass

    def create_form(self, obj=None):
        form = super(MyModelView, self).create_form(obj)
        form.uuid.data = uuid.uuid4()
        return form


class PostView(MyModelView):
    column_display_pk = True
    column_display_all_relations = True
    column_hide_backrefs = False
    column_list = ('id', 'title', 'posted_on', 'image', 'content', 'author_id', 'author')

    form_extra_fields = {
        'new_image': FileField('Upload Post Image', validators=[FileAllowed(['jpg', 'png'])]),
        'author_id': StringField('Author UUID', validators=[DataRequired()])
    }

    form_columns = (
        'title',
        'posted_on',
        'image',
        'new_image',
        'content',
        'author_id'
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
                try:
                    delete_image(self.img)
                except (FileNotFoundError, TypeError):
                    pass
            model.image = save_image(form.new_image)
        if form.author_id.data != current_user.uuid:
            try:
                user = User.query.get(form.author_id.data)
            except:
                raise ValidationError('User does not exist')
            form.author_id.data = user.uuid

    def on_model_delete(self, model: User):
        self.img = model.image

    def after_model_delete(self, model: User):
        try:
            delete_image(self.img)
        except (FileNotFoundError, TypeError):
            pass

    def create_form(self, obj=None):
        form = super(MyModelView, self).create_form(obj)
        form.author_id.data = current_user.uuid
        return form


class ServiceView(MyModelView):
    column_display_pk = True
    column_display_all_relations = True
    column_hide_backrefs = False
    column_list = ('id', 'name', 'duration')


class EntryView(MyModelView):
    column_display_pk = True
    column_display_all_relations = True
    column_hide_backrefs = False
    column_list = ('uuid', 'created_on', 'date', 'time', 'user_id', 'user.username')


admin.add_view(UserView(User, db.session))
admin.add_view(EntryView(Entry, db.session))
admin.add_view(PostView(Post, db.session))
admin.add_view(ServiceView(Service, db.session))
