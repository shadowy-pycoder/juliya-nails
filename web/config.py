import os
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
dotenv_db_path = os.path.join(os.path.dirname(__file__), ".env-db")

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

if os.path.exists(dotenv_db_path):
    load_dotenv(dotenv_db_path)


def manage_sensitive(name: str) -> str:
    with open(os.getenv(name)) as f:  # type: ignore
        return f.read().rstrip('\n')


class Config:
    SECRET_KEY = manage_sensitive('SECRET_KEY')
    MAIL_DEBUG = os.environ.get('MAIL_DEBUG')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    UPLOAD_FOLDER = 'static/images/'
    DEFAULT_AVATAR = 'default.jpg'
    APIFAIRY_TITLE = 'JuliyaNails API'
    APIFAIRY_VERSION = '1.0'
    APIFAIRY_UI = 'elements'
    APIFAIRY_UI_PATH = '/api/docs'
    DEBUG = False
    TESTING = False
    POSTGRES_USER = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD = manage_sensitive('POSTGRES_PASSWORD')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT')
    POSTGRES_DB = os.environ.get('POSTGRES_DB')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING_DB_NAME = os.environ.get('TESTING_DB_NAME')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{TESTING_DB_NAME}"
    TESTING = True


class ProductionConfig(Config):
    pass


def populate(cls: str = 'Config') -> dict:
    res = {}
    for k, v in dict(globals()).items():
        if k.endswith(cls) and k != cls:
            res[k[:-len(cls)].lower()] = v
    return res


config = populate()
