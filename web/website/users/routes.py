from datetime import datetime, timedelta
from urllib.parse import urlparse, ParseResult
from uuid import UUID

from flask import flash, render_template, redirect, url_for, session, Blueprint, request, current_app, abort
from flask_login import login_required
import phonenumbers
import sqlalchemy as sa
from sqlalchemy.sql import func
from werkzeug.wrappers.response import Response

from .. import db
from .forms import PasswordChangeForm, EmailChangeForm, EntryForm, UpdateProfileForm
from ..models import User, Entry, Service, current_user, get_or_404
from ..utils import send_email, email_confirmed, current_user_required, save_image, delete_image


users = Blueprint('users', __name__)


@users.route("/<username>/profile", methods=['GET'])
@login_required
@email_confirmed
def profile(username: str) -> Response | str:
    user = db.session.scalar(sa.select(User).filter_by(username=username)) or abort(404)
    prev_entry = db.session.scalar(
        user.entries.select()
        .filter(sa.or_(
            Entry.date < func.current_date(), sa.and_(
                Entry.date == func.current_date(),
                Entry.time <= func.current_time())))
        .order_by(Entry.date.desc(), Entry.time.desc()))
    next_entry = db.session.scalar(
        user.entries.select()
        .filter(sa.or_(
            Entry.date > func.current_date(), sa.and_(
                Entry.date == func.current_date(),
                Entry.time > func.current_time())))
        .order_by(Entry.date, Entry.time))
    form: dict[str, str | None] = {}
    for item in ['phone_number', 'viber', 'whatsapp']:
        try:
            p = phonenumbers.parse(getattr(user.socials, item))
        except phonenumbers.phonenumberutil.NumberParseException:
            form[item] = None
            continue
        formatted_number = phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        form[item] = formatted_number
    for item in ['vk', 'telegram', 'instagram']:
        form[item] = None
        url = getattr(user.socials, item)
        if url:
            parsed: ParseResult = urlparse(url=url)
            form[item] = parsed.path.strip('/')
    return render_template('users/profile.html',
                           title='Profile',
                           user=user,
                           form=form,
                           prev_entry=prev_entry,
                           next_entry=next_entry)


@users.route("/<username>/profile/change-password", methods=['GET', 'POST'])
@login_required
@email_confirmed
@current_user_required
def change_password_request(username: str) -> Response | str:
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


@users.route("/<username>/profile/change-email", methods=['GET', 'POST'])
@login_required
@email_confirmed
@current_user_required
def change_email_request(username: str) -> Response | str:
    form = EmailChangeForm()
    if form.validate_on_submit():
        session['new_email'] = form.email.data.lower()
        token = current_user.generate_token(context='change', salt_context='change-email')
        change_url = url_for('users.change_email', username=username, token=token, _external=True)
        template = 'users/email/change_email'
        subject = "Please confirm your email"
        send_email(form.email.data, subject, template, change_url=change_url, user=current_user)
        flash('An email with instructions to confirm your new email address has been sent.', 'info')
        return redirect(url_for('users.profile', username=username))
    return render_template('users/change_email.html', title='Change Email', legend='Change Email', form=form)


@users.route("/<username>/profile/change-email/<token>", methods=['GET', 'POST'])
@login_required
@email_confirmed
@current_user_required
def change_email(username: str, token: str | bytes) -> Response:
    if current_user.confirm_email_token(token, context='change', salt_context='change-email'):
        new_email = session.get('new_email')
        if new_email is not None:
            current_user.email = new_email
            db.session.add(current_user)
            db.session.commit()
            flash('Your email address has been updated.', 'success')
            return redirect(url_for('users.profile', username=username))
        else:
            flash('Something went wrong. Please try again.', 'danger')
            return redirect(url_for('users.change_email_request', username=username))
    else:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.change_email_request', username=username))


@users.route("/<username>/profile/create-entry", methods=['GET', 'POST'])
@login_required
@email_confirmed
@current_user_required
def create_entry(username: str) -> Response | str:
    user = db.session.scalar(sa.select(User).filter_by(username=username)) or abort(404)
    services = db.session.scalars(sa.select(Service)).all()
    form = EntryForm()
    form.services.choices = [(service.id, service.name) for service in services]
    if form.validate_on_submit():
        service_types = [
            db.session.execute(sa.select(Service).filter_by(id=service_id)).scalar_one()
            for service_id in form.services.data
        ]
        entry = Entry(date=form.date.data,
                      time=form.time.data,
                      user_id=current_user.uuid)
        entry.services.extend(service_types)
        prev_entry = db.session.scalar(
            sa.select(Entry)
            .filter(
                sa.and_(
                    Entry.date == entry.date,
                    Entry.time <= entry.time))
            .order_by(Entry.date.desc(), Entry.time.desc()))
        if prev_entry and prev_entry.ending_time > entry.timestamp:
            flash('Choose a different time (previous_entry)', 'danger')
            return render_template('users/create_entry.html', title='Profile', form=form, user=user)
        next_entry = db.session.scalar(
            sa.select(Entry)
            .filter(
                sa.and_(
                    Entry.date == entry.date,
                    Entry.time > entry.time))
            .order_by(Entry.date, Entry.time))
        if next_entry and next_entry.timestamp < entry.ending_time:
            flash('Choose a different time (next_entry)', 'danger')
            return render_template('users/create_entry.html', title='Profile', form=form, user=user)
        db.session.add(entry)
        db.session.commit()
        flash('New entry has been created.', 'success')
        return redirect(url_for('users.my_entries', username=username))
    return render_template('users/create_entry.html', title='Profile', form=form, user=user)


@users.route("/<username>/profile/edit-entry/<uuid:entry_id>", methods=['GET', 'POST'])
@login_required
@email_confirmed
@current_user_required
def edit_entry(username: str, entry_id: UUID) -> Response | str:
    entry = get_or_404(Entry, entry_id)
    if entry.user.username != username:
        abort(404)
    user = db.session.scalar(sa.select(User).filter_by(username=username)) or abort(404)
    services = db.session.scalars(sa.select(Service)).all()
    form = EntryForm()
    form.services.choices = [(service.id, service.name) for service in services]
    if form.validate_on_submit():
        service_types = [
            db.session.execute(sa.select(Service).filter_by(id=service_id)).scalar_one()
            for service_id in form.services.data
        ]
        entry.date = form.date.data
        entry.time = form.time.data
        entry.services.clear()
        entry.services.extend(service_types)
        prev_entry = db.session.scalar(
            sa.select(Entry)
            .filter(
                sa.and_(
                    Entry.date == entry.date,
                    Entry.time <= entry.time,
                    Entry.uuid != entry.uuid
                ))
            .order_by(Entry.date.desc(), Entry.time.desc()))
        if prev_entry and prev_entry.ending_time > entry.timestamp:
            flash('Choose a different time (previous entry)', 'danger')
            return render_template('users/edit_entry.html', title='Profile', form=form, user=user)
        next_entry = db.session.scalar(
            sa.select(Entry)
            .filter(
                sa.and_(
                    Entry.date == entry.date,
                    Entry.time > entry.time))
            .order_by(Entry.date, Entry.time))
        if next_entry and next_entry.timestamp < entry.ending_time:
            flash('Choose a different time(next_entry)', 'danger')
            return render_template('users/edit_entry.html', title='Profile', form=form, user=user)

        db.session.commit()
        flash('Your entry has been updated.', 'success')
        return redirect(url_for('users.my_entries', username=username))
    elif request.method == 'GET':
        flash(str(entry.ending_time))
    return render_template('users/edit_entry.html', title='Profile', form=form, user=user)


@ users.route("/<username>/profile/cancel-entry/<uuid:entry_id>", methods=['GET', 'POST'])
@ login_required
@ email_confirmed
@ current_user_required
def cancel_entry(username: str, entry_id: UUID) -> Response:
    entry = get_or_404(Entry, entry_id)
    if entry.user.username != username:
        abort(404)
    db.session.delete(entry)
    db.session.commit()
    flash('Your entry has been cancelled!', 'info')
    return redirect(url_for('users.my_entries', username=username))


@ users.route("/<username>/profile/my-entries", methods=['GET', 'POST'])
@ login_required
@ email_confirmed
@ current_user_required
def my_entries(username: str) -> str:
    entries = db.session.scalars(current_user.entries
                                 .select()
                                 .order_by(Entry.date.desc(), Entry.time.desc())).all()
    return render_template('users/my_entries.html', title='Profile', entries=entries)


@ users.route("/<username>/profile/update", methods=['GET', 'POST'])
@ login_required
@ email_confirmed
@ current_user_required
def update_profile(username: str) -> Response | str:
    user = db.session.scalar(sa.select(User).filter_by(username=username)) or abort(404)
    form = UpdateProfileForm()
    if form.validate_on_submit():
        for field in form._fields.values():
            if field.name not in ['delete_avatar', 'submit', 'csrf_token']:
                if field.data and field.name in ['instagram', 'telegram', 'vk']:
                    field.data = field.data.lower()
                elif field.data and field.name in ['first_name', 'last_name']:
                    field.data = field.data.capitalize()
                elif form.delete_avatar.data and field.name in ['avatar']:
                    delete_image(user.socials.avatar, path='profiles')
                    field.data = current_app.config['DEFAULT_AVATAR']
                elif field.data and field.name in ['avatar']:
                    delete_image(user.socials.avatar, path='profiles')
                    field.data = save_image(form.avatar, path='profiles')
                elif field.name in ['avatar']:
                    field.data = user.socials.avatar
                elif not field.data:
                    field.data = None
                setattr(user.socials, field.name, field.data)
        db.session.add(user.socials)
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('users.profile', username=username))
    elif request.method == 'GET':
        for field in form._fields.values():
            if field.name not in ['delete_avatar', 'submit', 'csrf_token']:
                field.data = getattr(user.socials, field.name)
    return render_template('users/update_profile.html',
                           title='Update Profile',
                           legend='Update Profile',
                           form=form, user=user)
