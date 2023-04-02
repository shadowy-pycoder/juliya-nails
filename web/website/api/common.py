from typing import Type, Any

from marshmallow import Schema
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence
from sqlalchemy.orm.decl_api import DeclarativeMeta

from .. import db, apifairy


@apifairy.process_apispec
def fields(spec: dict[str, dict]) -> dict[str, dict]:
    paths = spec['paths']
    for path in paths:
        if '{' not in path:
            path = paths.get(path)
            if 'get' in path:
                parameters = path['get']['parameters']
                if parameters:
                    for parameter in parameters:
                        if parameter['name'] in ['fields', 'sort']:
                            parameter['explode'] = False

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
                   model: Type[DeclarativeMeta],
                   mapping: dict[str, Type[Schema]]) -> tuple[Sequence, list | None]:
    only = None
    if fields:
        only = sanitize_fields(fields, mapping['fields'])
    data = sa.select(model)
    if filter:
        filters: dict = sanitize_fields(filter, mapping['filter'], param='filter')  # type: ignore[assignment]
        mapped_filters: dict = {getattr(model, param): value for param, value in filters.items()}
        data = data.filter(sa.and_(*[criterion == value for criterion, value in mapped_filters.items()]))
    if sort:
        criteria = sanitize_fields(sort, mapping['sort'], param='sort')
        data = data.order_by(sa.text(', '.join(criterion for criterion in criteria)))
    data = db.session.scalars(data).all()  # type: ignore[assignment]
    return data, only  # type: ignore[return-value]
