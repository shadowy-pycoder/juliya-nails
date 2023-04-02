from apifairy import authenticate, body, response, other_responses, arguments
from flask import Blueprint
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence

from ..common import sanitize_query
from ... import db, token_auth
from ...models import Service, get_or_404
from ...schemas import ServiceSchema, ServiceFieldSchema, ServiceSortSchema
from ...utils import admin_required

for_services = Blueprint('for_services', __name__)

service_schema = ServiceSchema()


@for_services.route('/services/', methods=['POST'])
@authenticate(token_auth)
@admin_required
@body(service_schema)
@response(service_schema, 201)
@other_responses({
    403: 'You are not allowed to perform this operation'
})
def create_one(kwargs: dict[str, str | float]) -> Service:
    """Create service"""
    service = Service(**kwargs)
    db.session.add(service)
    db.session.commit()
    return service


@for_services.route('/services/', methods=['GET'])
@authenticate(token_auth)
@arguments(ServiceFieldSchema(only=['fields']))
@arguments(ServiceSortSchema(only=['sort']))
@other_responses({200: 'OK'})
def get_all(fields: dict[str, list[str]],
            sort: dict[str, list[str]]) -> Sequence:
    """Get all services"""
    mapping = {'fields': ServiceFieldSchema, 'sort': ServiceSortSchema}
    services, only = sanitize_query(fields=fields,
                                    filter=None,
                                    sort=sort,
                                    model=Service,
                                    mapping=mapping)  # type: ignore[arg-type]
    return ServiceSchema(many=True, only=only).dump(services)


@for_services.route('/services/<int:service_id>', methods=['GET'])
@authenticate(token_auth)
@response(service_schema)
@other_responses({404: 'Service not found'})
def get_one(service_id: int) -> Service:
    """Retrieve service by id"""
    service = get_or_404(Service, service_id)
    return service


@for_services.route('/services/<int:service_id>', methods=['PUT'])
@authenticate(token_auth)
@admin_required
@body(service_schema)
@response(service_schema)
@other_responses({
    404: 'Service not found',
    403: 'You are not allowed to perform this operation'
})
def update_one(kwargs: dict, service_id: int) -> Service:
    """Update service"""
    service = get_or_404(Service, service_id)
    service.update(kwargs)
    db.session.commit()
    return service


@for_services.route('/services/<int:service_id>', methods=['DELETE'])
@authenticate(token_auth)
@admin_required
@other_responses({
    404: 'Service not found',
    403: 'You are not allowed to perform this operation'
})
def delete_one(service_id: int) -> tuple[str, int]:
    """Delete service"""
    service = get_or_404(Service, service_id)
    db.session.delete(service)
    db.session.commit()
    return '', 204
