import re

from marshmallow import validate, validates, validates_schema, \
    ValidationError, post_dump
import sqlalchemy as sa


from . import ma, db
# from api.auth import token_auth
from .models import User, Post, SocialMedia, Entry, Service
from .utils import PATTERNS


class UserSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = User

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.get_user', values={'user_id': '<uuid>'}, dump_only=True)
    username = ma.auto_field(required=True, validate=[validate.Length(min=2, max=20)])
    email = ma.auto_field(required=True, load_only=True, validate=[validate.Length(max=100),
                                                                   validate.Email()])
    password = ma.String(required=True, validate=validate.Length(min=8))
    registered_on = ma.auto_field(dump_only=True)
    confirmed = ma.auto_field(dump_only=True)
    confirmed_on = ma.auto_field(dump_only=True)
    posts = ma.URLFor('api.get_user_posts', values={'user_id': '<uuid>'}, dump_only=True)
    entries = ma.URLFor('api.get_user_entries', values={'user_id': '<uuid>'}, dump_only=True)
    socials = ma.URLFor('api.get_user_socials', values={'user_id': '<uuid>'}, dump_only=True)

    @validates('password')
    def validate_password(self, value: str) -> None:
        message = 'Password should contain at least '
        error_log = []
        errors = {
            '1 digit': re.search(r'\d', value) is None,
            '1 uppercase letter': re.search(r'[A-Z]', value) is None,
            '1 lowercase letter': re.search(r'[a-z]', value) is None,
            '1 special character': re.search(r'\W', value) is None,
        }
        for err_msg, error in errors.items():
            if error:
                error_log.append(err_msg)
        if error_log:
            raise ValidationError(message + ', '.join(err for err in error_log))

    @validates('username')
    def validate_username(self, value: str) -> None:
        pattern = re.compile(r"^[A-Za-z][A-Za-z0-9_.]*$")
        if not value[0].isalpha():
            raise ValidationError('Usernames must start with a letter')
        if not pattern.match(value):
            raise ValidationError('Usernames must have only letters, numbers, dots or underscores')
        user = db.session.scalar(sa.select(User).filter(User.username.ilike(value)))
        if user:
            raise ValidationError('Please choose a different username')

    @validates('email')
    def validate_email(self, value: str) -> None:
        user = db.session.scalar(sa.select(User).filter(User.email.ilike(value)))
        if user:
            raise ValidationError('Please choose a different email')


class SocilalMediaSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = SocialMedia

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.get_social', values={'social_id': '<uuid>'}, dump_only=True)
    user = ma.URLFor('api.get_user', values={'user_id': '<user_id>'}, dump_only=True)
    avatar = ma.auto_field(dump_only=True)
    first_name = ma.auto_field()
    last_name = ma.auto_field()
    phone_number = ma.auto_field()
    viber = ma.auto_field()
    whatsapp = ma.auto_field()
    instagram = ma.Url()
    telegram = ma.Url()
    youtube = ma.Url()
    website = ma.Url()
    vk = ma.Url()
    about = ma.auto_field()

    @validates('first_name')
    def validate_first_name(self, value: str) -> None:
        pattern = re.compile(PATTERNS['name'])
        if not pattern.match(value):
            raise ValidationError('Invalid value for first name')

    @validates('last_name')
    def validate_last_name(self, value: str) -> None:
        pattern = re.compile(PATTERNS['name'])
        if not pattern.match(value):
            raise ValidationError('Invalid value for last name')

    @validates('phone_number')
    def validate_phone_number(self, value: str) -> None:
        pattern = re.compile(PATTERNS['phone_number'])
        if not pattern.match(value):
            raise ValidationError('Invalid value for phone number')

    @validates('viber')
    def validate_viber(self, value: str) -> None:
        pattern = re.compile(PATTERNS['phone_number'])
        if not pattern.match(value):
            raise ValidationError('Invalid value for Viber')

    @validates('whatsapp')
    def validate_whatsapp(self, value: str) -> None:
        pattern = re.compile(PATTERNS['phone_number'])
        if not pattern.match(value):
            raise ValidationError('Invalid value for WhatsApp')

    @validates('instagram')
    def validate_instagram(self, value: str) -> None:
        pattern = re.compile(PATTERNS['instagram'])
        if not pattern.match(value):
            raise ValidationError('Invalid value for Instagram')

    @validates('telegram')
    def validate_telegram(self, value: str) -> None:
        pattern = re.compile(PATTERNS['telegram'])
        if not pattern.match(value):
            raise ValidationError('Invalid value for Telegram')

    @validates('youtube')
    def validate_youtube(self, value: str) -> None:
        pattern = re.compile(PATTERNS['youtube'])
        if not pattern.match(value):
            raise ValidationError('Invalid value for YouTube')

    @validates('website')
    def validate_website(self, value: str) -> None:
        pattern = re.compile(PATTERNS['website'])
        if not pattern.match(value):
            raise ValidationError('Invalid value for website')

    @validates('vk')
    def validate_vk(self, value: str) -> None:
        pattern = re.compile(PATTERNS['vk'])
        if not pattern.match(value):
            raise ValidationError('Invalid value for VK')


class PostSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = Post
    id = ma.auto_field(dump_only=True)
    url = ma.URLFor('api.get_post', values={'post_id': '<id>'}, dump_only=True)
    title = ma.auto_field()
    content = ma.auto_field()
    image = ma.auto_field(dump_only=True)
    posted_on = ma.auto_field(dump_only=True)
    author = ma.URLFor('api.get_user', values={'user_id': '<author_id>'}, dump_only=True)


class EntrySchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = Entry

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.get_entry', values={'entry_id': '<uuid>'}, dump_only=True)
    user = ma.URLFor('api.get_user', values={'user_id': '<user_id>'}, dump_only=True)
    services = ma.URLFor('api.get_entry_services', values={'entry_id': '<uuid>'}, dump_only=True)
    created_on = ma.auto_field(dump_only=True)
    date = ma.auto_field(required=True)
    time = ma.auto_field(required=True)


class ServiceSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = Service

    id = ma.auto_field(dump_only=True)
    url = ma.URLFor('api.get_service', values={'service_id': '<id>'}, dump_only=True)
    name = ma.auto_field(required=True)
    duration = ma.auto_field(reuired=True)
    entries = ma.URLFor('api.get_service_entries', values={'service_id': '<id>'}, dump_only=True)


class TokenShema(ma.Schema):  # type: ignore[name-defined]
    token = ma.String()
