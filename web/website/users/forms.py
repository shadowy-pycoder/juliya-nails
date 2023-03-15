from flask_admin.form import DateTimePickerWidget
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField, DateField, TimeField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, Email, EqualTo

from ..auth.forms import CustomValidatorsMixin


class PasswordChangeForm(CustomValidatorsMixin, FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Password')


class EmailChangeForm(CustomValidatorsMixin, FlaskForm):

    email = StringField('New Email',
                        validators=[DataRequired(), Email(), Length(max=100)])
    old_password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email')


class EntryForm(CustomValidatorsMixin, FlaskForm):

    services = SelectMultipleField('Choose Service', validators=[
                                   DataRequired()], id='multiselect', render_kw={"data-placeholder": "Choose service..."})
    date = DateField('local', validators=[DataRequired()], id='datepicker')
    time = TimeField('Time', validators=[DataRequired()], id='timepicker')
    submit = SubmitField('Update Email')
