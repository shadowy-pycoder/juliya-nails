from typing import Type, Any

from marshmallow import Schema
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.orm import WriteOnlyCollection

from .. import db, apifairy
from ..models import Entry


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


def sanitize_fields(fields: dict[str, list[str]] | dict[str, str],
                    schema: Type[Schema],
                    param: str = 'fields'
                    ) -> list | dict:
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
                   mapping: dict[str, Type[Schema]]
                   ) -> tuple[Sequence, list | None, dict[str, int]]:
    if not fields or not (only := sanitize_fields(fields, mapping['fields'])):
        only = None
    data = obj.select() if isinstance(obj, WriteOnlyCollection) else sa.select(obj)
    if filter:
        filters: dict[str, str] = sanitize_fields(filter, mapping['filter'], param='filter')  # type: ignore[assignment]
        mapped_filters: list[tuple] = []
        for param, value in filters.items():
            if param.endswith(('_gte', '_lte')):
                mapped_filters.append((getattr(model, param[:-4]), value, param[-4:]))
            elif param.endswith(('_gt', '_lt')):
                mapped_filters.append((getattr(model, param[:-3]), value, param[-3:]))
            else:
                mapped_filters.append((getattr(model, param), value))
        conditions = []
        for mapped_filter in mapped_filters:
            if len(mapped_filter) == 3:
                criterion, value, operator = mapped_filter
                if operator == '_gte':
                    conditions.append(criterion >= value)
                elif operator == '_lte':
                    conditions.append(criterion <= value)
                elif operator == '_gt':
                    conditions.append(criterion > value)
                elif operator == '_lt':
                    conditions.append(criterion < value)
            else:
                criterion, value = mapped_filter
                if isinstance(value, str):
                    conditions.append(criterion.ilike(value))
                else:
                    conditions.append(criterion == value)
        data = data.filter(sa.and_(*conditions))
    if sort:
        criteria = sanitize_fields(sort, mapping['sort'], param='sort')
        data = data.order_by(sa.text(', '.join(criterion for criterion in criteria)))
    count = db.session.scalar(sa.select(sa.func.count()).select_from(data.subquery()))
    if not count:
        pagination['total'] = 0
        pagination['last_page'] = 1
        offset = 0
    else:
        pagination['total'] = count
        quotient, remainder = divmod(pagination['total'], pagination['per_page'])
        pagination['last_page'] = quotient + 1 if remainder else quotient
        if pagination['page'] > pagination['last_page']:
            pagination['page'] = pagination['last_page']
        offset = (pagination['page'] - 1) * pagination['per_page']
    data = data.limit(pagination['per_page']).offset(offset)
    data = db.session.scalars(data).all()  # type: ignore[assignment]
    return data, only, pagination  # type: ignore[return-value]


def can_create_entry(entry: Entry, context: str = 'create') -> bool:
    filters = [Entry.date == entry.date, Entry.time <= entry.time]
    if context == 'update':
        filters.append(Entry.uuid != entry.uuid)
    prev_entry = db.session.scalar(
        sa.select(Entry)
        .filter(
            sa.and_(*filters))
        .order_by(Entry.date.desc(), Entry.time.desc()))
    if prev_entry and prev_entry.ending_time > entry.timestamp:
        return False
    next_entry = db.session.scalar(
        sa.select(Entry)
        .filter(
            sa.and_(
                Entry.date == entry.date,
                Entry.time > entry.time))
        .order_by(Entry.date, Entry.time))
    if next_entry and next_entry.timestamp < entry.ending_time:
        return False
    return True
