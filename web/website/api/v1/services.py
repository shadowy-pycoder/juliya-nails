from flask import jsonify
from flask.wrappers import Response
import sqlalchemy as sa

from . import api
from ... import db
from ...models import Service, Entry, get_or_404


@api.route('/services/')
def get_services() -> Response:
    services = db.session.scalars(sa.select(Service)).all()
    return jsonify({'services': [service.to_json() for service in services]})


@api.route('/services/<int:service_id>')
def get_service(service_id: int) -> Response:
    service = get_or_404(Service, service_id)
    return jsonify(service.to_json())


@api.route('/services/<int:service_id>/entries/')
def get_service_entries(service_id: str) -> Response:
    service = get_or_404(Service, service_id)
    entries = db.session.scalars(service.entries.select().order_by(Entry.date.desc(), Entry.time.desc())).all()
    return jsonify({'entries': [entry.to_json() for entry in entries]})
