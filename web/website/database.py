from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from sqlalchemy.orm.decl_api import DeclarativeMeta


class SQLAlchemy:

    def __init__(self) -> None:
        self.Model: DeclarativeMeta = declarative_base()

    def init_app(self, app: Flask):
        self.create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
        self.create_scoped_session()

    def create_engine(self, sqlalchemy_database_uri: str):
        self.engine = create_engine(sqlalchemy_database_uri)

    def create_scoped_session(self):
        self.session = scoped_session(
            sessionmaker(autocommit=False, bind=self.engine)
        )
