from apifairy import authenticate, body, response, other_responses
from flask import jsonify, Blueprint
from flask.wrappers import Response
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence

from ... import db, token_auth
from ...models import Service, Entry, get_or_404
from ...schemas import ServiceSchema

for_services = Blueprint('for_services', __name__)

service_schema = ServiceSchema()
services_schema = ServiceSchema(many=True)


@for_services.route('/services/')
@response(services_schema)
def get_services() -> Sequence:
    services = db.session.scalars(sa.select(Service)).all()
    return services  # type: ignore[return-value]


@for_services.route('/services/<int:service_id>')
@response(service_schema)
def get_service(service_id: int) -> Response:
    service = get_or_404(Service, service_id)
    return service


from .entries import entries_schema  # nopep8


@for_services.route('/services/<int:service_id>/entries')
@response(entries_schema)
def get_service_entries(service_id: int) -> Sequence:
    service = get_or_404(Service, service_id)
    entries = db.session.scalars(service.entries.select().order_by(Entry.date.desc(), Entry.time.desc())).all()
    return entries  # type: ignore[return-value]
