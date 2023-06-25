import os

from website import create_app, db

app = create_app(os.environ.get('FLASK_CONFIG') or 'production')
