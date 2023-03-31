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
@authenticate(token_auth)
@response(services_schema)
def get_all() -> Sequence:
    services = db.session.scalars(sa.select(Service)).all()
    return services  # type: ignore[return-value]


@for_services.route('/services/<int:service_id>')
@authenticate(token_auth)
@response(service_schema)
def get_one(service_id: int) -> Response:
    service = get_or_404(Service, service_id)
    return service
