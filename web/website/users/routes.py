from flask import flash, render_template, redirect, url_for, session, Blueprint
from flask_login import current_user, login_required

from .forms import PasswordChangeForm, EmailChangeForm, EntryForm
from ..models import User
from ..utils import send_email, email_confirmed
from .. import db


users = Blueprint('users', __name__)


@users.route("/profile/<username>", methods=['GET', 'POST'])
@login_required
@email_confirmed
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EntryForm()
    return render_template('users/profile.html', title='Profile', form=form, user=user)


@users.route("/change-password", methods=['GET', 'POST'])
@login_required
@email_confirmed
def change_password_request():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        current_user.password = form.new_password.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your password has been updated.', 'success')
        return redirect(url_for('users.profile'))
    return render_template('users/change_password.html', title='Change Password', legend='Change Password', form=form)

@users.route("/change-email", methods=['GET', 'POST'])
@login_required
@email_confirmed
def change_email_request():
    form = EmailChangeForm()
    if form.validate_on_submit():
        session['new_email'] = form.email.data
        token = current_user.generate_token(context='change', salt_context='change-email')
        change_url = url_for('users.change_email', token=token, _external=True)
        template = 'users/email/change_email'
        subject = "Please confirm your email"
        send_email(form.email.data, subject, template, change_url=change_url, user=current_user)
        flash('An email with instructions to confirm your new email address has been sent.', 'info')
    return render_template('users/change_email.html', title='Change Email', legend='Change Email', form=form)


@users.route("/change-email/<token>", methods=['GET', 'POST'])
@login_required
def change_email(token):
    if current_user.confirm_email_token(token, context='change', salt_context='change-email'):
        new_email = session.get('new_email')
        if new_email is not None:
            current_user.email = new_email
            db.session.add(current_user)
            db.session.commit()
            flash('Your email address has been updated.', 'success')
            return redirect(url_for('users.profile'))
        else:
            flash('Something went wrong. Please try again.', 'danger')
            return redirect(url_for('users.change_email_request'))
    else:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.change_email_request'))
