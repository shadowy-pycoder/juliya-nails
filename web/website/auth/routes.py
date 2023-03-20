from urllib.parse import urlparse, urljoin

from flask import abort, flash, render_template, redirect, url_for, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required

from .forms import (RegistrationForm, LoginForm, PasswordResetRequestForm,
                    PasswordResetForm)
from ..models import User, SocialMedia
from ..utils import send_email
from .. import db

auth = Blueprint('auth', __name__)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            confirmed=False,
        )
        db.session.add(user)
        db.session.commit()
        token = user.generate_token()
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        template = 'auth/email/confirm_email'
        subject = "Please confirm your email"
        send_email(user.email, subject, template, confirm_url=confirm_url)
        login_user(user)
        socials = SocialMedia(user_id=current_user.uuid)
        db.session.add(socials)
        db.session.commit()
        flash(f'A confirmation email has been sent to {user.email}.', 'info')
        return redirect(url_for("auth.unconfirmed"))
    return render_template('auth/register.html', title='Register', legend='Register', form=form)


@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user: User = User.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if not is_safe_url(next_page):
                return abort(400)
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('auth/login.html', title='Login', legend='Login', form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@auth.route('/confirm/<token>')
@login_required
def confirm_email(token):
    if current_user.confirmed:
        flash('Account already confirmed.', 'info')
    elif current_user.confirm_email_token(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'danger')
    return redirect(url_for('main.home'))


@auth.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('main.home'))
    return render_template('auth/unconfirmed.html')


@auth.route('/resend')
@login_required
def resend_confirmation():
    token = current_user.generate_token()
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    template = 'auth/email/confirm_email'
    subject = "Please confirm your email"
    send_email(current_user.email, subject, template, confirm_url=confirm_url)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('auth.unconfirmed'))


@auth.route('/reset-request', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.home'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        flash('An email with instructions to reset your password has been sent.', 'info')
        user: User = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            token = user.generate_token(
                context='reset',
                salt_context='reset-password')
            reset_url = url_for('auth.password_reset_token', token=token, _external=True)
            template = 'auth/reset_password'
            subject = 'Reset your password'
            send_email(user.email, subject, template, reset_url=reset_url)
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_request.html',
                           title='Reset Request',
                           legend='Password Reset Request',
                           form=form)


@auth.route("/reset-password/<token>", methods=['GET', 'POST'])
def password_reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user: User = User.reset_password_token(token)
        if user:
            user.password = form.password.data
            db.session.add(user)
            db.session.commit()
            flash('Your password has been updated! You are now able to log in', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('That is an invalid or expired token', 'warning')
            return redirect(url_for('auth.password_reset_request'))
    return render_template('auth/reset_password.html',
                           title='Reset Password',
                           legend='Reset Password',
                           form=form)
