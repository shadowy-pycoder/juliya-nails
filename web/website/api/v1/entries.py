from flask import jsonify
from flask.wrappers import Response
import sqlalchemy as sa

from . import api
from ... import db
from ...models import Entry, get_or_404


@api.route('/entries/')
def get_entries() -> Response:
    entries = db.session.scalars(sa.select(Entry).order_by(Entry.date.desc(), Entry.time.desc())).all()
    return jsonify({'entries': [entry.to_json() for entry in entries]})


@api.route('/entries/<entry_id>')
def get_entry(entry_id: str) -> Response:
    entry = get_or_404(Entry, entry_id)
    return jsonify(entry.to_json())


@api.route('/entries/<entry_id>/services/')
def get_entry_services(entry_id: str) -> Response:
    entry = get_or_404(Entry, entry_id)
    return jsonify({'services': [service.to_json() for service in entry.services]})
