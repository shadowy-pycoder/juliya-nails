from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, SelectMultipleField, DateField, TimeField,
                     URLField, TextAreaField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, Optional

from ..auth.forms import CustomValidatorsMixin, IntegrityCheck
from ..models import User


class PasswordChangeForm(CustomValidatorsMixin, FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Password')


class EmailChangeForm(CustomValidatorsMixin, FlaskForm):

    email = StringField('New Email',
                        validators=[DataRequired(), Email(), Length(max=100), IntegrityCheck(model=User)])
    old_password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email')


class EntryForm(CustomValidatorsMixin, FlaskForm):

    services = SelectMultipleField('Choose Service', validators=[
                                   DataRequired()], id='multiselect', render_kw={"data-placeholder": "Choose service..."})
    date = DateField('local', validators=[DataRequired()], id='datepicker')
    time = TimeField('Time', validators=[DataRequired()], id='timepicker')
    submit = SubmitField('Update Email')


class UpdateProfileForm(CustomValidatorsMixin, FlaskForm):
    youtube = URLField('Youtube',
                       validators=[Optional(), Length(max=255), Regexp('(https?:\/\/)?(www\.)?youtu((\.be)|(be\..{2,5}))\/((user)|(channel))\/',
                                                                       message='Please enter a valid YouTube link'), IntegrityCheck()],
                       render_kw={"placeholder": "https://www.youtube.com/channel/"})
    website = URLField('Website', validators=[Optional(), Length(max=255), IntegrityCheck()],
                       render_kw={"placeholder": "https://www.example.com/"})
    vk = URLField('VK',
                  validators=[Optional(), Length(max=255), Regexp('(https?:\/\/|https:\/\/)?(www.)?(vk\.com|vkontakte\.ru)\/(id\d|[a-zA-Z0-9_.])+',
                                                                  message='Please enter a valid VK link'), IntegrityCheck()],
                  render_kw={"placeholder": "https://vk.com/username"})
    telegram = URLField('Telegram',
                        validators=[Optional(), Length(max=255), Regexp('(?:@|(?:(?:(?:https?://)?t(?:elegram)?)\.me\/))(\w{4,})',
                                                                        message='Please enter a valid Telegram link'), IntegrityCheck()],
                        render_kw={"placeholder": "https://t.me/username"})
    instagram = URLField('Instagram',
                         validators=[Optional(), Length(max=255), Regexp('(?:(?:http|https):\/\/)?(?:www.)?(?:instagram.com|instagr.am|instagr.com)\/(\w+)',
                                                                         message='Please enter a valid Instagram link'), IntegrityCheck()],
                         render_kw={"placeholder": "https://instagram.com/username"})
    about = TextAreaField('About', validators=[Optional(), Length(max=255)],
                          render_kw={"placeholder": "Enter information about you"})
    phone_number = StringField('Phone', id='phone', validators=[Optional(), Length(max=50), IntegrityCheck()])
    viber = StringField('Viber', id='viber', validators=[Optional(), Length(max=50), IntegrityCheck()])
    whatsapp = StringField('WhatsApp', id='whatsapp', validators=[Optional(), Length(max=50), IntegrityCheck()])
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)],
                             render_kw={"placeholder": "Enter first name"})
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)],
                            render_kw={"placeholder": "Enter last name"})
    submit = SubmitField('Update Profile')
