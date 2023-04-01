from apifairy import APIFairy
from flask import Flask
from flask_admin import Admin
from flask_bcrypt import Bcrypt
from flask_ckeditor import CKEditor
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from flask_login import LoginManager
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate

from .database import SQLAlchemy
from config import config

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
admin = Admin(name='Admin Panel', template_mode='bootstrap4')
mail = Mail()
ckeditor = CKEditor()
apifairy = APIFairy()
ma = Marshmallow()
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


def create_app(config_name: str) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    admin.init_app(app)
    mail.init_app(app)
    ckeditor.init_app(app)
    apifairy.init_app(app)
    ma.init_app(app)

    from .api.v1 import api as api_v1, auth as api_auth, errors
    from .api.v1.entries import for_entries
    from .api.v1.posts import for_posts
    from .api.v1.services import for_services
    from .api.v1.socials import for_socials
    from .api.v1.users import for_users
    from .auth.routes import auth
    from .main.routes import main, handle_error
    from .models import add_admin_views, User, UUID_, AnonymousUser
    from .users.routes import users

    @app.before_request
    def before_request() -> None:
        db.session()

    @app.teardown_appcontext
    def shutdown_session(response_or_exc) -> None:  # type: ignore[no-untyped-def]
        db.session.remove()

    @login_manager.user_loader
    def load_user(user_id: UUID_) -> User | None:
        return db.session.get(User, user_id)

    login_manager.anonymous_user = AnonymousUser
    add_admin_views(db.session)
    api_v1.register_blueprint(for_entries)
    api_v1.register_blueprint(for_posts)
    api_v1.register_blueprint(for_services)
    api_v1.register_blueprint(for_socials)
    api_v1.register_blueprint(for_users)
    app.register_blueprint(api_v1, url_prefix='/api/v1')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main, url_prefix='/')
    app.register_blueprint(users, url_prefix='/users')
    app.register_error_handler(404, handle_error)
    app.register_error_handler(405, handle_error)
    return app
