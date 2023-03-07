import re

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

from ..users.models import User
from website import bcrypt

class CustomValidatorsMixin:

    def validate_password(self, password: FlaskForm):
        message = 'Password should contain at least '
        error_log = []
        errors = {
            '1 digit': re.search(r'\d', password.data) is None,
            '1 uppercase letter': re.search(r'[A-Z]', password.data) is None,
            '1 lowercase letter': re.search(r'[a-z]', password.data) is None,
            '1 special character': re.search(r'\W', password.data) is None,
        }
        for err_msg, error in errors.items():
            if error:
                error_log.append(err_msg)
        if error_log:
            raise ValidationError(message + ', '.join(err for err in error_log))
            
    def validate_old_password(self, old_password: FlaskForm):
        if not bcrypt.check_password_hash(current_user.password, old_password.data):
            raise ValidationError('Entered password is incorrect. Please try again')
    
    def validate_new_password(self, new_password: FlaskForm):
        self.validate_password(new_password)
        if new_password.data == self.old_password.data:
            raise ValidationError('Your new password must be different from your old password.')
        
            
    def validate_username(self, username: FlaskForm):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email: FlaskForm):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class RegistrationForm(CustomValidatorsMixin, FlaskForm):

    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(), Length(max=100)])
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

