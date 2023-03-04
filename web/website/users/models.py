import uuid

from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from website import db, login_manager


@login_manager.user_loader
def load_user(uuid):
    return User.query.get(uuid)


class User(db.Model, UserMixin):

    __tablename__ = 'user'

    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    date = db.Column(db.String(50), nullable=False, default=func.now())

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}', '{self.date})"

    def get_id(self):
        return (self.uuid)
