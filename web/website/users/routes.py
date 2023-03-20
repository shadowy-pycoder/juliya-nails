from flask import flash, render_template, redirect, url_for, session, Blueprint, request
from flask_login import current_user, login_required

from .forms import PasswordChangeForm, EmailChangeForm, EntryForm, UpdateProfileForm
from ..models import User, Entry, Service, SocialMedia
from ..utils import send_email, email_confirmed, current_user_required
from .. import db


users = Blueprint('users', __name__)


@users.route("/profile/<username>", methods=['GET', 'POST'])
@login_required
@email_confirmed
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EntryForm()
    return render_template('users/profile.html', title='Profile', form=form, user=user)


@users.route("/profile/<username>/change-password", methods=['GET', 'POST'])
@login_required
@email_confirmed
@current_user_required
def change_password_request(username):
    form = PasswordChangeForm()
    if form.validate_on_submit():
        current_user.password = form.new_password.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your password has been updated.', 'success')
        return redirect(url_for('users.profile', username=username))
    return render_template('users/change_password.html',
                           title='Change Password',
                           legend='Change Password', form=form)


@users.route("/profile/<username>/change-email", methods=['GET', 'POST'])
@login_required
@email_confirmed
@current_user_required
def change_email_request(username):
    form = EmailChangeForm()
    if form.validate_on_submit():
        session['new_email'] = form.email.data
        token = current_user.generate_token(context='change', salt_context='change-email')
        change_url = url_for('users.change_email', username=username, token=token, _external=True)
        template = 'users/email/change_email'
        subject = "Please confirm your email"
        send_email(form.email.data, subject, template, change_url=change_url, user=current_user)
        flash('An email with instructions to confirm your new email address has been sent.', 'info')
        return redirect(url_for('users.profile', username=username))
    return render_template('users/change_email.html', title='Change Email', legend='Change Email', form=form)


@users.route("profile/<username>/change-email/<token>", methods=['GET', 'POST'])
@login_required
def change_email(username, token):
    if current_user.confirm_email_token(token, context='change', salt_context='change-email'):
        new_email = session.get('new_email')
        if new_email is not None:
            current_user.email = new_email
            db.session.add(current_user)
            db.session.commit()
            flash('Your email address has been updated.', 'success')
            return redirect(url_for('users.profile', username=current_user.username))
        else:
            flash('Something went wrong. Please try again.', 'danger')
            return redirect(url_for('users.change_email_request', username=current_user.username))
    else:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.change_email_request', username=current_user.username))


@users.route("/profile/<username>/create-entry", methods=['GET', 'POST'])
@login_required
@email_confirmed
@current_user_required
def create_entry(username):
    user = User.query.filter_by(username=username).first_or_404()
    services = Service.query.all()
    form = EntryForm()
    form.services.choices = [service.name for service in services]
    if form.validate_on_submit():
        service_types = [
            Service.query.filter_by(name=service_type).first()
            for service_type in form.services.data
        ]
        entry = Entry(date=form.date.data,
                      time=form.time.data,
                      user_id=current_user.uuid)
        entry.services.extend(service_types)
        db.session.add(entry)
        db.session.commit()
        flash('New entry has been created.', 'success')
        return redirect(url_for('users.profile', username=current_user.username))
    return render_template('users/create_entry.html', title='Profile', form=form, user=user)


@users.route("/profile/<username>/my-entries", methods=['GET', 'POST'])
@login_required
@email_confirmed
@current_user_required
def my_entries(username):
    entries = current_user.entries.all()
    services = Service.query.all()
    return render_template('users/my_entries.html', title='Profile', entries=entries, services=services)


@users.route("/profile/<username>/update", methods=['GET', 'POST'])
@login_required
@email_confirmed
@current_user_required
def update_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    socials: SocialMedia = SocialMedia.query.filter_by(user_id=current_user.uuid).first()
    form = UpdateProfileForm()
    if form.validate_on_submit():
        for field in form._fields.values():
            if field.name not in ['submit', 'csrf_token']:
                if not field.data:
                    field.data = None
                setattr(socials, field.name, field.data)
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('users.profile', username=current_user.username))
    elif request.method == 'GET':
        for field in form._fields.values():
            if field.name not in ['submit', 'csrf_token']:
                field.data = getattr(socials, field.name)
    return render_template('users/update_profile.html',
                           title='Update Profile',
                           legend='Update Profile',
                           form=form, user=user)
