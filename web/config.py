import os
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), ".env")

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URI']
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
    APIFAIRY_UI = 'swagger_ui'
    APIFAIRY_UI_PATH = '/api/docs'


class DevelopmentConfig(Config):
    DEBUG = True


def populate(cls: str = 'Config') -> dict:
    res = {}
    for k, v in dict(globals()).items():
        if k.endswith(cls) and k != cls:
            res[k.rstrip(cls).lower()] = v
    return res


config = populate()
