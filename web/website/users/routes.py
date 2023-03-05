from datetime import datetime
from urllib.parse import urlparse, urljoin

from flask import abort, flash, render_template, redirect, url_for, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required

from .forms import RegistrationForm, LoginForm
from .models import User
from .utils import send_email
from website import bcrypt, db


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


users = Blueprint('users', __name__)


@users.route("/register/", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        password_hash = bcrypt.generate_password_hash(form.password.data).decode('UTF-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=password_hash,
            confirmed=False,
        )
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        confirm_url = url_for('users.confirm_email', token=token, _external=True)
        html = render_template('activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(user.email, subject, html)
        login_user(user)
        flash(f'A confirmation email has been sent to {current_user.email}.', 'info')
        return redirect(url_for("main.home"))
    return render_template('register.html', title='Register', form=form)


@users.route("/login/", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if not is_safe_url(next_page):
                return abort(400)
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route("/logout/")
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route("/account/")
@login_required
def account():
    return render_template('account.html', title='Account')


@users.route('/confirm/<token>')
@login_required
def confirm_email(token):
    try:
        email = User.confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'info')
    else:
        user.confirmed = True
        user.confirmed_on = datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('main.home'))
