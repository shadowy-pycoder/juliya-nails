from uuid import UUID

from apifairy import authenticate, body, response, other_responses
from flask import jsonify
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence

from . import api

from ... import db
from ...models import Entry, get_or_404
from ...schemas import EntrySchema


entry_schema = EntrySchema()
entries_schema = EntrySchema(many=True)


@api.route('/entries', methods=['POST'])
@body(entry_schema)
@response(entry_schema, 201)
def create_entry(kwargs: dict[str, str]) -> Entry:
    entry = Entry(**kwargs)
    db.session.add(entry)
    db.session.commit()
    return entry


@api.route('/entries')
@response(entries_schema)
def get_entries() -> Sequence:
    entries = db.session.scalars(sa.select(Entry).order_by(Entry.date.desc(), Entry.time.desc())).all()
    return entries  # type: ignore[return-value]


@api.route('/entries/<uuid:entry_id>')
@response(entry_schema)
def get_entry(entry_id: UUID) -> Entry:
    entry = get_or_404(Entry, entry_id)
    return entry


from .services import services_schema  # nopep8


@api.route('/entries/<uuid:entry_id>/services/')
@response(services_schema)
def get_entry_services(entry_id: UUID) -> Sequence:
    entry = get_or_404(Entry, entry_id)
    return entry.services  # type: ignore[return-value]
