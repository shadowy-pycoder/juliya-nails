from collections.abc import Callable
from functools import wraps
import os
import secrets
from threading import Thread
from typing import ParamSpec, TypeVar, Any

from flask import current_app, flash, redirect, url_for, render_template, Flask, abort
from flask_mail import Message
from flask_wtf.file import FileField
from PIL import Image
from werkzeug.wrappers.response import Response

from . import mail
from .models import current_user

P = ParamSpec("P")
R = TypeVar("R")


def send_async_email(app: Flask, msg: Message) -> None:
    with app.app_context():
        mail.send(msg)


def send_email(to: str, subject: str, template: str, **kwargs: str) -> Thread:
    app = current_app._get_current_object()  # type: ignore[attr-defined]
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


def email_confirmed(func: Callable[P, R]) -> Callable[P, R | Response]:
    @wraps(func)
    def decorated_function(*args: P.args, **kwargs: P.kwargs) -> R | Response:
        if not current_user.confirmed:
            flash('Please confirm your account!', 'warning')
            return redirect(url_for('users.unconfirmed'))
        return func(*args, **kwargs)
    return decorated_function


def admin_required(func: Callable[P, R]) -> Callable[P, R | Response]:
    @wraps(func)
    def decorated_function(*args: P.args, **kwargs: P.kwargs) -> R | Response:
        if current_user.is_anonymous or not current_user.admin:
            return abort(404)
        return func(*args, **kwargs)
    return decorated_function


def current_user_required(func: Callable[..., R]) -> Callable[..., R | Response]:
    @wraps(func)
    def decorated_function(username: str, *args: Any, **kwargs: Any) -> R | Response:
        if username != current_user.username:
            return redirect(url_for(f'users.{func.__name__}', username=current_user.username, **kwargs))
        return func(username, *args, **kwargs)
    return decorated_function


def save_image(file: FileField, path: str = 'posts') -> str:
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


def delete_image(filename: str, path: str = 'posts') -> None:
    if filename != current_app.config['DEFAULT_AVATAR']:
        try:
            img_path = os.path.join(
                current_app.root_path,
                current_app.config['UPLOAD_FOLDER'],
                path,
                filename)
            os.unlink(img_path)
        except (FileNotFoundError, TypeError):
            pass
