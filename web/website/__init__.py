from flask import Flask
from flask_admin import Admin
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config


db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
admin = Admin(name='JuliyaNails Admin', template_mode='bootstrap4')


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    admin.init_app(app)
    from .main.routes import main
    from .users.routes import users
    app.register_blueprint(main, url_prefix='/')
    app.register_blueprint(users, url_prefix='/')
    return app
