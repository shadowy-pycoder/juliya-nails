from uuid import UUID

from apifairy import authenticate, body, response, other_responses
from flask import jsonify, request
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence

from . import api
from ... import db, token_auth
from ...models import Entry, User, Service, get_or_404
from ...schemas import EntrySchema, CreateEntrySchema


entry_schema = EntrySchema()
entries_schema = EntrySchema(many=True)
create_entry_schema = CreateEntrySchema()


@api.route('/entries/', methods=['POST'])
@authenticate(token_auth)
@body(create_entry_schema)
@response(entry_schema, 201)
def create_entry(kwargs: dict) -> Entry:
    user: User = token_auth.current_user()
    services = {
        db.session.get(Service, service_id)
        for service_id in kwargs['services']
    }
    entry = Entry(user_id=user.uuid)
    entry.services.update(service for service in services if service)
    entry.date = kwargs['date']
    entry.time = kwargs['time']
    db.session.add(entry)
    db.session.commit()
    return entry


@api.route('/entries/')
@response(entries_schema)
def get_entries() -> Sequence:
    entries = db.session.scalars(sa.select(Entry).order_by(Entry.date.desc(), Entry.time.desc())).all()
    return entries  # type: ignore[return-value]


@api.route('/entries/<uuid:entry_id>')
@response(entry_schema)
def get_entry(entry_id: UUID) -> Entry:
    entry = get_or_404(Entry, entry_id)
    return entry


@api.route('/users/<uuid:user_id>/entries')
@authenticate(token_auth)
@response(entries_schema)
def get_user_entries(user_id: UUID) -> Sequence:
    user = get_or_404(User, user_id)
    entries = db.session.scalars(user.entries.select().order_by(Entry.date.desc(), Entry.time.desc())).all()
    return entries  # type: ignore[return-value]


@api.route('/me/entries', methods=['GET'])
@authenticate(token_auth)
@response(entries_schema)
def my_entries() -> Sequence:
    """Retrieve my entries"""
    user: User = token_auth.current_user()
    entries = db.session.scalars(user.entries.select().order_by(Entry.date.desc(), Entry.time.desc())).all()
    return entries  # type: ignore[return-value]
