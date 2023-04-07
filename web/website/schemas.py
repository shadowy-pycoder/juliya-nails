from datetime import datetime, date
import re
from typing import Any, Type

from marshmallow import validate, validates, ValidationError, post_load, Schema
import sqlalchemy as sa
from webargs import fields
from werkzeug.exceptions import Forbidden, NotFound

from . import ma, db, token_auth
from .models import User, Post, SocialMedia, Entry, Service
from .utils import PATTERNS

paginated_cache: dict[Type[Schema], Type[Schema]] = {}


class UserSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = User
        description = 'This schema represents a user.'

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.for_users.get_one', values={'user_id': '<uuid>'}, dump_only=True)
    username = ma.auto_field(required=True, validate=[validate.Length(min=2, max=20)])
    email = ma.Email(required=True, validate=[validate.Length(max=100)], load_only=True)
    password = ma.String(required=True, validate=validate.Length(min=8), load_only=True)
    registered_on = ma.auto_field(dump_only=True)
    confirmed = ma.auto_field(dump_only=True)
    confirmed_on = ma.auto_field(dump_only=True)
    posts = ma.URLFor('api.for_posts.get_user_posts', values={'user_id': '<uuid>'}, dump_only=True)
    entries = ma.URLFor('api.for_entries.get_user_entries', values={'user_id': '<uuid>'}, dump_only=True)
    socials = ma.URLFor('api.for_socials.get_user_socials', values={'user_id': '<uuid>'}, dump_only=True)

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


class AdminUserSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = User
        description = 'This schema represents a user.'

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.for_users.get_one', values={'user_id': '<uuid>'}, dump_only=True)
    username = ma.auto_field(required=True, validate=[validate.Length(min=2, max=20)])
    email = ma.Email(required=True, validate=[validate.Length(max=100)])
    password = ma.String(required=True, validate=validate.Length(min=8), load_only=True)
    registered_on = ma.auto_field()
    confirmed = ma.auto_field()
    confirmed_on = ma.auto_field()
    posts = ma.URLFor('api.for_posts.get_user_posts', values={'user_id': '<uuid>'}, dump_only=True)
    entries = ma.URLFor('api.for_entries.get_user_entries', values={'user_id': '<uuid>'}, dump_only=True)
    socials = ma.URLFor('api.for_socials.get_user_socials', values={'user_id': '<uuid>'}, dump_only=True)

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
    username = ma.auto_field(load_only=True)
    old_password = ma.String(load_only=True, validate=validate.Length(min=3))

    @validates('old_password')
    def validate_old_password(self, value: str) -> None:
        if not token_auth.current_user().verify_password(value):
            raise ValidationError('Password is incorrect')


class UserInfoSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = User

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.for_users.get_one', values={'user_id': '<uuid>'}, dump_only=True)
    username = ma.auto_field(dump_only=True)


class SocialMediaSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = SocialMedia

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.for_socials.get_one', values={'social_id': '<uuid>'}, dump_only=True)
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


class PostSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = Post
    id = ma.auto_field(dump_only=True)
    url = ma.URLFor('api.for_posts.get_one', values={'post_id': '<id>'}, dump_only=True)
    title = ma.auto_field()
    content = ma.auto_field()
    image = ma.auto_field(dump_only=True)
    posted_on = ma.auto_field(dump_only=True)
    author = ma.Nested(UserInfoSchema(), dump_only=True)


class ServiceSchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = Service

    id = ma.auto_field(dump_only=True)
    url = ma.URLFor('api.for_services.get_one', values={'service_id': '<id>'}, dump_only=True)
    name = ma.auto_field(required=True)
    duration = ma.auto_field(required=True)
    entries = ma.URLFor('api.for_entries.get_service_entries', values={'service_id': '<id>'}, dump_only=True)

    @post_load
    def fix_name(self, data: dict[str, str], **kwargs: dict[str, Any]) -> dict[str, str]:
        if 'name' in data:
            data['name'] = data['name'].capitalize()
        return data

    @validates('duration')
    def validate_duration(self, value: float) -> None:
        if round(value, 2) <= 0:
            raise ValidationError('Duration must be greater than or equal to 0.1')


class TokenSchema(ma.Schema):  # type: ignore[name-defined]
    token = ma.String()


class EntrySchema(ma.SQLAlchemySchema):  # type: ignore[name-defined]
    class Meta:
        model = Entry

    uuid = ma.UUID(dump_only=True)
    url = ma.URLFor('api.for_entries.get_one', values={'entry_id': '<uuid>'}, dump_only=True)
    user = ma.Nested(UserInfoSchema(), dump_only=True)
    services = ma.Nested(ServiceSchema(many=True), dump_only=True)
    created_on = ma.auto_field(dump_only=True)
    date = ma.auto_field(required=True)
    time = ma.auto_field(required=True)


class CreateEntrySchema(EntrySchema):  # type: ignore[name-defined]
    class Meta:
        model = Entry

    services = ma.List(ma.Integer(), required=True)

    @validates('date')
    def validate_date(self, value: datetime) -> None:
        if value < date.today():
            raise ValidationError('Date cannot be lower than current date')


class EmptySchema(ma.Schema):  # type: ignore[name-defined]
    pass


class UserFieldSchema(ma.Schema):  # type: ignore[name-defined]
    uuid = ma.String()
    url = ma.String()
    username = ma.String()
    registered_on = ma.String()
    confirmed = ma.String()
    confirmed_on = ma.String()
    posts = ma.String()
    entries = ma.String()
    socials = ma.String()
    fields = fields.DelimitedList(ma.String(),
                                  description=("""
                                                List of fields to include in response
                                                Possible values:
                                                "uuid",
                                                "url",
                                                "username",
                                                "registered_on",
                                                "confirmed",
                                                "confirmed_on",
                                                "posts",
                                                "entries",
                                                "socials"
                                                """))


class UserFilterSchema(ma.Schema):  # type: ignore[name-defined]
    username = ma.String(description=("""
                                        Find user by username
                                        """))
    confirmed = ma.Boolean(validate=validate.OneOf([True, False]),
                           description=("""
                                        Possible values:
                                        "true",
                                        "false",
                                        """))
    confirmed_on = ma.DateTime(description=("""
                                            Format:
                                            "confirmed_on=2023-03-27 15:00"
                                            """))
    confirmed_on_gte = ma.DateTime(data_key='confirmed_on[gte]',
                                   description=("""
                                            Format:
                                            "confirmed_on[gte]=2023-03-27 15:00"
                                            """))
    confirmed_on_lte = ma.DateTime(data_key='confirmed_on[lte]',
                                   description=("""
                                            Format:
                                            "confirmed_on[lte]=2023-03-27 15:00"
                                            """))
    confirmed_on_gt = ma.DateTime(data_key='confirmed_on[gt]',
                                  description=("""
                                            Format:
                                            "confirmed_on[gt]=2023-03-27 15:00"
                                            """))
    confirmed_on_lt = ma.DateTime(data_key='confirmed_on[lt]',
                                  description=("""
                                            Format:
                                            "confirmed_on[lt]=2023-03-27 15:00"
                                            """))


class UserSortSchema(ma.Schema):  # type: ignore[name-defined]
    username = ma.String()
    registered_on = ma.DateTime()
    confirmed_on = ma.DateTime()
    sort = fields.DelimitedList(ma.String(),
                                load_default=['registered_on'],
                                description=("""
                                                Possible values:
                                                "username",
                                                "registered_on",
                                                "confirmed_on",
                                                """))


class SocialsFieldSchema(SocialMediaSchema):  # type: ignore[name-defined]
    fields = fields.DelimitedList(ma.String(),
                                  description=("""
                                                Possible values:
                                                "uuid",
                                                "url",
                                                "user",
                                                "avatar",
                                                "first_name",
                                                "last_name",
                                                "phone_number",
                                                "viber",
                                                "whatsapp",
                                                "instagram",
                                                "telegram",
                                                "youtube",
                                                "website",
                                                "vk",
                                                "about"
                                                """))


class SocialsFilterSchema(ma.Schema):  # type: ignore[name-defined]
    first_name = ma.String(description=("""
                                        Filter by specified first name
                                        """))
    last_name = ma.String(description=("""
                                        Filter by specified last name
                                        """))


class SocialsSortSchema(ma.Schema):  # type: ignore[name-defined]
    first_name = ma.String()
    last_name = ma.String()
    sort = fields.DelimitedList(ma.String(),
                                load_default=['first_name'],
                                description=("""
                                                Possible values:
                                                "first_name",
                                                "last_name",
                                                """))


class ServiceFieldSchema(ServiceSchema):  # type: ignore[name-defined]
    fields = fields.DelimitedList(ma.String(),
                                  description=("""
                                                Possible values:
                                                "id",
                                                "url",
                                                "name",
                                                "duration",
                                                "entries",
                                                """))


class ServiceFilterSchema(ma.Schema):  # type: ignore[name-defined]
    duration = ma.Float(description=("""
                                    Format:
                                    "duration=2"
                                    """))
    duration_gte = ma.Float(data_key='duration[gte]',
                            description=("""
                                            Format:
                                            "duration[gte]=1"
                                            """))
    duration_lte = ma.Float(data_key='duration[lte]',
                            description=("""
                                            Format:
                                            "duration[lte]=3"
                                            """))
    duration_gt = ma.Float(data_key='duration[gt]',
                           description=("""
                                            Format:
                                            "duration[gt]=1"
                                            """))
    duration_lt = ma.Float(data_key='duration[lt]',
                           description=("""
                                            Format:
                                            "duration[lt]=3"
                                            """))


class ServiceSortSchema(ma.Schema):  # type: ignore[name-defined]
    name = ma.String()
    duration = ma.String()
    sort = fields.DelimitedList(ma.String(),
                                load_default=['name'],
                                description=("""
                                                Possible values:
                                                "name",
                                                "duration"
                                                """))


class PostFieldSchema(PostSchema):  # type: ignore[name-defined]
    fields = fields.DelimitedList(ma.String(),
                                  description=("""
                                                Possible values:
                                                "id",
                                                "url",
                                                "title",
                                                "content",
                                                "image",
                                                "posted_on",
                                                "author,
                                                """))


class PostFilterSchema(ma.Schema):  # type: ignore[name-defined]
    posted_on = ma.DateTime(description=("""
                                            Format:
                                            "posted_on=2023-03-27 15:00"
                                            """))
    posted_on_gte = ma.DateTime(data_key='posted_on[gte]',
                                description=("""
                                            Format:
                                            "posted_on[gte]=2023-03-27 15:00"
                                            """))
    posted_on_lte = ma.DateTime(data_key='posted_on[lte]',
                                description=("""
                                            Format:
                                            "posted_on[lte]=2023-03-27 15:00"
                                            """))
    posted_on_gt = ma.DateTime(data_key='posted_on[gt]',
                               description=("""
                                            Format:
                                            "posted_on[gt]=2023-03-27 15:00"
                                            """))
    posted_on_lt = ma.DateTime(data_key='posted_on[lt]',
                               description=("""
                                            Format:
                                            "posted_on[lt]=2023-03-27 15:00"
                                            """))


class PostSortSchema(ma.Schema):  # type: ignore[name-defined]
    title = ma.String()
    posted_on = ma.String()
    sort = fields.DelimitedList(ma.String(),
                                load_default=['-posted_on'],
                                description=("""
                                                Possible values:
                                                "title",
                                                "posted_on"
                                                """))


class EntryFieldSchema(EntrySchema):  # type: ignore[name-defined]
    fields = fields.DelimitedList(ma.String(),
                                  description=("""
                                                Possible values:
                                                "uuid",
                                                "url",
                                                "user",
                                                "services",
                                                "created_on",
                                                "date",
                                                "time",
                                                """))


class EntryFilterSchema(ma.Schema):  # type: ignore[name-defined]
    date = ma.Date(description=("""
                                        Format:
                                        "date=2023-03-27"
                                        """))
    date_gte = ma.Date(data_key='date[gte]',
                       description=("""
                                        Format:
                                        "date[gte]=2023-03-27"
                                        """))
    date_lte = ma.Date(data_key='date[lte]',
                       description=("""
                                        Format:
                                        "date[lte]=2023-03-27"
                                        """))
    date_gt = ma.Date(data_key='date[gt]',
                      description=("""
                                        Format:
                                        "date[gt]=2023-03-27"
                                        """))
    date_lt = ma.Date(data_key='date[lt]',
                      description=("""
                                        Format:
                                        "date[lt]=2023-03-27"
                                        """))
    time = ma.Time(description=("""
                                    Format:
                                    "time=15:00"
                                    """))

    time_gte = ma.Time(data_key='time[gte]',
                       description=("""
                                    Format:
                                    "time[gte]=15:00"
                                    """))
    time_lte = ma.Time(data_key='time[lte]',
                       description=("""
                                    Format:
                                    "time[lte]=15:00"
                                    """))
    time_gt = ma.Time(data_key='time[gt]',
                      description=("""
                                    Format:
                                    "time[gt]=15:00"
                                    """))
    time_lt = ma.Time(data_key='time[lt]',
                      description=("""
                                    Format:
                                    "time[lt]=15:00"
                                    """))


class EntrySortSchema(ma.Schema):  # type: ignore[name-defined]
    created_on = ma.String()
    date = ma.String()
    time = ma.String()
    sort = fields.DelimitedList(ma.String(),
                                load_default=['-date'],
                                description=("""
                                                Possible values:
                                                "created_on",
                                                "date",
                                                "time"
                                                """))


class PaginationSchema(ma.Schema):  # type: ignore[name-defined]
    class Meta:
        ordered = True
    page = ma.Integer(load_default=1)
    per_page = ma.Integer(load_default=25)
    last_page = ma.Integer(load_default=1, dump_only=True)
    total = ma.Integer(dump_only=True)

    @validates('page')
    def validate_page(self, value: int) -> None:
        if value <= 0:
            raise ValidationError('Page number cannot be lower than 1')

    @validates('per_page')
    def validate_per_page(self, value: int) -> None:
        if not (0 < value <= 50):
            raise ValidationError('Results per page parameter should be a positive number no greater than 50')


def PaginatedSchema(
        schema: Type[Schema],
        pagination_schema: Type[Schema] = PaginationSchema
) -> Type[Schema]:
    if schema in paginated_cache:
        return paginated_cache[schema]

    class PaginateSchema(ma.Schema):  # type: ignore[name-defined]
        class Meta:
            ordered = True
        pagination = ma.Nested(pagination_schema)
        results = ma.Nested(schema, many=True)
    PaginateSchema.__name__ = f'Paginated{schema.__class__.__name__}'
    paginated_cache[schema] = PaginateSchema
    return PaginateSchema


class NotFoundSchema(ma.Schema):  # type: ignore[name-defined]
    class Meta:
        ordered = True
    error = NotFound()
    code = ma.Integer(load_default=error.code)
    message = ma.String(load_default=error.name)
    description = ma.String(load_default=error.description)


class ForbiddenSchema(ma.Schema):  # type: ignore[name-defined]
    class Meta:
        ordered = True
    error = Forbidden()
    code = ma.Integer(load_default=error.code)
    message = ma.String(load_default=error.name)
    description = ma.String(load_default=error.description)
