from typing import Type, Any

from marshmallow import Schema
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.orm import WriteOnlyCollection

from .. import db, apifairy


@apifairy.process_apispec
def fields(spec: dict[str, dict | Any]) -> dict[str, dict]:
    paths = ['/api/v1/posts',
             '/api/v1/users',
             '/api/v1/entries',
             '/api/v1/services',
             '/api/v1/socials',
             '/api/v1/me/posts',
             '/api/v1/me/entries',
             '/api/v1/users/{user_id}/posts',
             '/api/v1/users/{user_id}/entries',
             '/api/v1/services/{service_id}/entries']
    for path in paths:
        operation = spec['paths'].get(path, {})
        if 'get' in operation:
            parameters = operation['get']['parameters']
            if parameters:
                for parameter in parameters:
                    if parameter['name'] in ['fields', 'sort']:
                        parameter['explode'] = False
            get_responses = operation['get']['responses']
            if '204' in get_responses:
                del get_responses['204']
        if 'post' in operation:
            post_responses = operation['post']['responses']
            if '204' in post_responses:
                del post_responses['204']
    return spec


def sanitize_fields(fields: dict[str, list[str]] | dict[str, Any],
                    schema: Type[Schema],
                    param: str = 'fields') -> list | dict:
    formatted_fields = set()
    if param == 'fields':
        for field in fields[param]:
            if field in schema().fields.keys() and field != param:
                formatted_fields.add(field)
    elif param == 'filter':
        filters = {}
        for field, value in fields.items():
            if field in schema().fields.keys():
                filters.update({field: value})
        return filters  # type: ignore[return-value]
    elif param == 'sort':
        for field in fields[param]:
            if field.lstrip('-') in schema().fields.keys() and field.lstrip('-') != param:
                if field.startswith('-'):
                    field = field.lstrip('-') + ' DESC'
                formatted_fields.add(field)
    return list(formatted_fields)


def sanitize_query(fields: dict[str, list[str]] | None,
                   filter: dict[str, Any] | None,
                   sort: dict[str, list[str]] | None,
                   pagination: dict[str, int],
                   obj: Type[DeclarativeMeta] | WriteOnlyCollection,
                   model: Type[DeclarativeMeta],
                   mapping: dict[str, Type[Schema]]) -> tuple[Sequence, list | None, dict[str, int]]:
    only = sanitize_fields(fields, mapping['fields']) if fields else None
    data = obj.select() if isinstance(obj, WriteOnlyCollection) else sa.select(obj)
    if filter:
        filters: dict = sanitize_fields(filter, mapping['filter'], param='filter')  # type: ignore[assignment]
        mapped_filters: dict = {getattr(model, param): value for param, value in filters.items()}
        data = data.filter(sa.and_(*[criterion == value for criterion, value in mapped_filters.items()]))
    if sort:
        criteria = sanitize_fields(sort, mapping['sort'], param='sort')
        data = data.order_by(sa.text(', '.join(criterion for criterion in criteria)))
    count = db.session.scalar(sa.select(sa.func.count()).select_from(data.subquery()))
    pagination['total'] = count if count else 0
    quotient, remainder = divmod(pagination['total'], pagination['per_page'])
    pagination['last_page'] = quotient + 1 if remainder else quotient
    if pagination['page'] > pagination['last_page']:
        pagination['page'] = pagination['last_page']
    data = data.limit(pagination['per_page']).offset((pagination['page']-1)*pagination['per_page'])
    data = db.session.scalars(data).all()  # type: ignore[assignment]
    return data, only, pagination  # type: ignore[return-value]
