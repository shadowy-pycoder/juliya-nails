from datetime import datetime, date
import re

from marshmallow import validate, validates, validates_schema, \
    ValidationError, post_dump, pre_load, post_load, pre_dump
import sqlalchemy as sa


from . import ma, db, token_auth
from .models import User, Post, SocialMedia, Entry, Service
from .utils import PATTERNS


class UserSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = User

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.get_user', values={'user_id': '<uuid>'}, dump_only=True)
    username = ma.auto_field(required=True, validate=[validate.Length(min=2, max=20)], dump_only=True)
    email = ma.Email(required=True, validate=[validate.Length(max=100)], load_only=True)
    password = ma.String(required=True, validate=validate.Length(min=8), load_only=True)
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


class UpdateUserSchema(UserSchema):
    old_password = ma.String(load_only=True, validate=validate.Length(min=3))

    @validates('old_password')
    def validate_old_password(self, value: str) -> None:
        if not token_auth.current_user().verify_password(value):
            raise ValidationError('Password is incorrect')


class UserInfoSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = User

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.get_user', values={'user_id': '<uuid>'}, dump_only=True)
    username = ma.auto_field(dump_only=True)


class SocialMediaSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = SocialMedia

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.get_social', values={'social_id': '<uuid>'}, dump_only=True)
    user = ma.Nested(UserInfoSchema(), dump_only=True)
    avatar = ma.auto_field(dump_only=True)
    first_name = ma.auto_field(validate=[validate.Regexp(
        PATTERNS['name'], error='Invalid value for first name')])
    last_name = ma.auto_field(validate=[validate.Regexp(
        PATTERNS['name'], error='Invalid value for last name')])
    phone_number = ma.auto_field(validate=[validate.Regexp(
        PATTERNS['phone_number'], error='Invalid value for phone number')])
    viber = ma.auto_field(validate=[validate.Regexp(
        PATTERNS['phone_number'], error='Invalid value for Viber')])
    whatsapp = ma.auto_field(validate=[validate.Regexp(
        PATTERNS['phone_number'], error='Invalid value for WhatsApp')])
    instagram = ma.Url(validate=[validate.Regexp(
        PATTERNS['instagram'], error='Invalid value for Instagram')])
    telegram = ma.Url(validate=[validate.Regexp(
        PATTERNS['telegram'], error='Invalid value for Telegram')])
    youtube = ma.Url(validate=[validate.Regexp(
        PATTERNS['youtube'], error='Invalid value for YouTube')])
    website = ma.Url(validate=[validate.Regexp(
        PATTERNS['website'], error='Invalid value for website')])
    vk = ma.Url(validate=[validate.Regexp(
        PATTERNS['vk'], error='Invalid value for VK')])
    about = ma.auto_field()

    # @validates('first_name')
    # def validate_first_name(self, value: str) -> None:
    #     pattern = re.compile(PATTERNS['name'])
    #     if not pattern.match(value):
    #         raise ValidationError('Invalid value for first name')

    # @validates('last_name')
    # def validate_last_name(self, value: str) -> None:
    #     pattern = re.compile(PATTERNS['name'])
    #     if not pattern.match(value):
    #         raise ValidationError('Invalid value for last name')

    # @validates('phone_number')
    # def validate_phone_number(self, value: str) -> None:
    #     pattern = re.compile(PATTERNS['phone_number'])
    #     if not pattern.match(value):
    #         raise ValidationError('Invalid value for phone number')

    # @validates('viber')
    # def validate_viber(self, value: str) -> None:
    #     pattern = re.compile(PATTERNS['phone_number'])
    #     if not pattern.match(value):
    #         raise ValidationError('Invalid value for Viber')

    # @validates('whatsapp')
    # def validate_whatsapp(self, value: str) -> None:
    #     pattern = re.compile(PATTERNS['phone_number'])
    #     if not pattern.match(value):
    #         raise ValidationError('Invalid value for WhatsApp')

    # @validates('instagram')
    # def validate_instagram(self, value: str) -> None:
    #     pattern = re.compile(PATTERNS['instagram'])
    #     if not pattern.match(value):
    #         raise ValidationError('Invalid value for Instagram')

    # @validates('telegram')
    # def validate_telegram(self, value: str) -> None:
    #     pattern = re.compile(PATTERNS['telegram'])
    #     if not pattern.match(value):
    #         raise ValidationError('Invalid value for Telegram')

    # @validates('youtube')
    # def validate_youtube(self, value: str) -> None:
    #     pattern = re.compile(PATTERNS['youtube'])
    #     if not pattern.match(value):
    #         raise ValidationError('Invalid value for YouTube')

    # @validates('website')
    # def validate_website(self, value: str) -> None:
    #     pattern = re.compile(PATTERNS['website'])
    #     if not pattern.match(value):
    #         raise ValidationError('Invalid value for website')

    # @validates('vk')
    # def validate_vk(self, value: str) -> None:
    #     pattern = re.compile(PATTERNS['vk'])
    #     if not pattern.match(value):
    #         raise ValidationError('Invalid value for VK')


class PostSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = Post
    id = ma.auto_field(dump_only=True)
    url = ma.URLFor('api.get_post', values={'post_id': '<id>'}, dump_only=True)
    title = ma.auto_field()
    content = ma.auto_field()
    image = ma.auto_field(dump_only=True)
    posted_on = ma.auto_field(dump_only=True)
    author = ma.Nested(UserInfoSchema(), dump_only=True)


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


class EntrySchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = Entry

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.get_entry', values={'entry_id': '<uuid>'}, dump_only=True)
    user = ma.Nested(UserInfoSchema(), dump_only=True)
    services = ma.Nested(ServiceSchema(many=True), dump_only=True)
    created_on = ma.auto_field(dump_only=True)
    date = ma.auto_field(required=True)
    time = ma.auto_field(required=True)


class CreateEntrySchema(EntrySchema):  # type: ignore[name-defined]
    class Meta:
        model = Entry

    services = ma.List(ma.Integer())

    @validates('date')
    def validate_date(self, value: datetime) -> None:
        if value < date.today():
            raise ValidationError('Date cannot be lower than current date')
