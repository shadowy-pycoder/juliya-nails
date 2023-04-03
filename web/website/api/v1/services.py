from apifairy import authenticate, body, response, other_responses, arguments
from flask import Blueprint, jsonify, url_for
from flask.wrappers import Response

from ..common import sanitize_query
from ... import db, token_auth
from ...models import Service, get_or_404
from ...schemas import ServiceSchema, ServiceFieldSchema, ServiceSortSchema
from ...utils import admin_required

for_services = Blueprint('for_services', __name__)

service_schema = ServiceSchema()
services_schema = ServiceSchema(many=True)


@for_services.route('/services', methods=['POST'])
@authenticate(token_auth)
@admin_required
@body(service_schema)
@other_responses({
    201: service_schema,
    403: 'You are not allowed to perform this operation'
})
def create_one(kwargs: dict[str, str | float]) -> Response:
    """Create service"""
    service = Service(**kwargs)
    db.session.add(service)
    db.session.commit()
    response = jsonify(service_schema.dump(service))
    response.status_code = 201
    response.headers['Location'] = url_for('api.for_services.get_one', service_id=service.id, _external=True)
    return response


@for_services.route('/services', methods=['GET'])
@authenticate(token_auth)
@arguments(ServiceFieldSchema(only=['fields']))
@arguments(ServiceSortSchema(only=['sort']))
@other_responses({200: services_schema})
def get_all(fields: dict[str, list[str]],
            sort: dict[str, list[str]]) -> Response:
    """Get all services"""
    mapping = {'fields': ServiceFieldSchema, 'sort': ServiceSortSchema}
    services, only = sanitize_query(fields=fields,
                                    filter=None,
                                    sort=sort,
                                    obj=Service,
                                    model=Service,
                                    mapping=mapping)  # type: ignore[arg-type]
    return ServiceSchema(many=True, only=only).dump(services)


@for_services.route('/services/<int:service_id>', methods=['GET'])
@authenticate(token_auth)
@response(service_schema)
@other_responses({404: 'Service not found'})
def get_one(service_id: int) -> Response:
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
def update_one(kwargs: dict, service_id: int) -> Response:
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
