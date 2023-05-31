from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (StringField, PasswordField, SubmitField, SelectMultipleField, DateField, TimeField,
                     URLField, TextAreaField, BooleanField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, Optional

from ..auth.forms import CustomValidatorsMixin, IntegrityCheck
from ..models import User
from ..utils import PATTERNS


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
                                   DataRequired()
                                   ], id='multiselect', render_kw={"data-placeholder": "Choose service..."},
                                   choices=[], coerce=int)
    date = DateField('Date', validators=[DataRequired()], id='datepicker')
    time = TimeField('Time', validators=[DataRequired()], id='timepicker')
    submit = SubmitField('Create Entry')


class UpdateProfileForm(CustomValidatorsMixin, FlaskForm):
    youtube = URLField('Youtube',
                       validators=[
                           Optional(),
                           Length(max=255),
                           Regexp(PATTERNS['youtube'],
                                  message='Please enter a valid YouTube link'),
                           IntegrityCheck()
                       ],
                       render_kw={"placeholder": "https://www.youtube.com/channel/"})
    website = URLField('Website',
                       validators=[
                           Optional(),
                           Length(max=255),
                           IntegrityCheck()
                       ],
                       render_kw={"placeholder": "https://www.example.com/"})
    vk = URLField('VK',
                  validators=[
                      Optional(),
                      Length(max=255),
                      Regexp(PATTERNS['vk'],
                             message='Please enter a valid VK link'),
                      IntegrityCheck()
                  ],
                  render_kw={"placeholder": "https://vk.com/username"})
    telegram = URLField('Telegram',
                        validators=[
                            Optional(),
                            Length(max=255),
                            Regexp(PATTERNS['telegram'],
                                   message='Please enter a valid Telegram link'),
                            IntegrityCheck()
                        ],
                        render_kw={"placeholder": "https://t.me/username"})
    instagram = URLField('Instagram',
                         validators=[
                             Optional(),
                             Length(max=255),
                             Regexp(PATTERNS['instagram'],
                                    message='Please enter a valid Instagram link'),
                             IntegrityCheck()
                         ],
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
    avatar = FileField('Upload Profile Image', validators=[Optional(), FileAllowed(['jpg', 'png'])])
    delete_avatar = BooleanField('Set profile image to default')
    submit = SubmitField('Update Profile')
