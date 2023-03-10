from flask import Flask
from flask_admin import Admin
from flask_bcrypt import Bcrypt
from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


from config import Config


db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
admin = Admin(name='JuliyaNails Admin', template_mode='bootstrap4')
mail = Mail()
ckeditor = CKEditor()



def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.config['UPLOADS_DEFAULT_DEST'] = 'static/images'
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    admin.init_app(app)
    mail.init_app(app)
    ckeditor.init_app(app)
    
    from .main.routes import main, page_not_found
    from .auth.routes import auth
    from .users.routes import users
    app.register_blueprint(main, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(users, url_prefix='/users')
    app.register_error_handler(404, page_not_found)
    return app
