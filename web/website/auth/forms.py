import re
from typing import Protocol, Type

import phonenumbers
from flask_wtf import FlaskForm
import sqlalchemy as sa
from wtforms import StringField, PasswordField, SubmitField, BooleanField, Field
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp

from .. import bcrypt, db
from ..models import User, SocialMedia, current_user
from ..utils import PATTERNS


class HasValueProtocol(Protocol):

    @property
    def old_password(self) -> Field: ...

    def validate_password(self, password: Field) -> None: ...


class CustomValidatorsMixin:

    def validate_password(self, password: Field) -> None:
        message = 'Please add at least '
        errors = {
            '1 digit': re.search(r'\d', password.data) is None,
            '1 uppercase letter': re.search(r'[A-Z]', password.data) is None,
            '1 lowercase letter': re.search(r'[a-z]', password.data) is None,
            '1 special character': re.search(r'\W', password.data) is None,
        }
        for err_msg, error in errors.items():
            if error:
                password.errors.append(message + err_msg)

    def validate_old_password(self, old_password: Field) -> None:
        if not bcrypt.check_password_hash(current_user.password_hash, old_password.data):
            raise ValidationError('Entered password is incorrect. Please try again')

    def validate_new_password(self: HasValueProtocol, new_password: Field) -> None:
        self.validate_password(new_password)
        if new_password.data == self.old_password.data:
            raise ValidationError('Your new password must be different from your old password.')

    def validate_phone_number(self, phone_number: Field) -> None:
        try:
            p = phonenumbers.parse(phone_number.data)
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError('Invalid phone number')

    def validate_viber(self, viber: Field) -> None:
        self.validate_phone_number(viber)

    def validate_whatsapp(self, whatsapp: Field) -> None:
        self.validate_phone_number(whatsapp)


class IntegrityCheck:
    def __init__(self, message: str | None = None,
                 model: Type[SocialMedia] = SocialMedia) -> None:
        if not message:
            message = 'Already exists. Please choose a different one.'
        self.message = message
        self.model = model

    def __call__(self, form: FlaskForm, field: Field) -> None:
        if self.model == SocialMedia:
            query = db.session.scalar(sa.select(self.model).filter_by(**{field.name: field.data}))
            if query and query.user_id != current_user.uuid:
                raise ValidationError(self.message)
        elif self.model == User:
            query = db.session.scalar(sa.select(self.model)
                                      .filter(self.model.username
                                              .ilike(field.data)))
            if query:
                raise ValidationError(self.message)


class RegistrationForm(CustomValidatorsMixin, FlaskForm):

    username = StringField(
        'Username', validators=[
            DataRequired(),
            Length(min=2, max=20),
            Regexp(PATTERNS['username'],
                   message='Usernames must have only letters, numbers, dots or underscores'),
            IntegrityCheck(model=User)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(), Length(max=100), IntegrityCheck(model=User)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email(), Length(max=100)])
    submit = SubmitField('Reset Password')


class PasswordResetForm(CustomValidatorsMixin, FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
