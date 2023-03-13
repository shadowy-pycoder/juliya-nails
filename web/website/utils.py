import os
import secrets
from functools import wraps
from threading import Thread

from flask import current_app, flash, redirect, url_for, render_template, Flask, abort
from flask_login import current_user
from flask_mail import Message
from flask_wtf.file import FileField
from PIL import Image

from . import mail


def send_async_email(app: Flask, msg: Message):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_DEFAULT_SENDER'])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


def email_confirmed(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.confirmed:
            flash('Please confirm your account!', 'warning')
            return redirect(url_for('users.unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function


def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous or not current_user.admin:
            return abort(404)
        return func(*args, **kwargs)
    return decorated_function


def save_image(file: FileField, path='posts'):
    _, f_ext = os.path.splitext(file.data.filename)
    filename = secrets.token_hex(8) + f_ext
    img_path = os.path.join(
        current_app.root_path,
        current_app.config['UPLOAD_FOLDER'],
        path,
        filename)
    if path != 'posts':
        output_size = (150, 150)
        img = Image.open(file.data)
        img.thumbnail(output_size)
        img.save(img_path)
        return filename
    file.data.save(img_path)
    return filename


def delete_image(filename, path='posts'):
    img_path = os.path.join(
        current_app.root_path,
        current_app.config['UPLOAD_FOLDER'],
        path,
        filename)
    os.unlink(img_path)
