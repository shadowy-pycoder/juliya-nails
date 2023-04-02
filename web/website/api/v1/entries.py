from uuid import UUID

from apifairy import authenticate, body, response, other_responses, arguments
from flask import Blueprint, abort
from sqlalchemy.sql.schema import Sequence

from ..common import sanitize_query
from ... import db, token_auth
from ...models import Entry, User, Service, get_or_404
from ...schemas import EntrySchema, CreateEntrySchema, EntryFieldSchema, EntrySortSchema
from ...utils import admin_required

for_entries = Blueprint('for_entries', __name__)

entry_schema = EntrySchema()
entries_schema = EntrySchema(many=True)
create_entry_schema = CreateEntrySchema()
update_entry_schema = CreateEntrySchema(partial=True)


@for_entries.route('/entries/', methods=['POST'])
@authenticate(token_auth)
@body(create_entry_schema)
@response(entry_schema, 201)
def create_one(kwargs: dict) -> Entry:
    """Create new entry"""
    user: User = token_auth.current_user()
    services = {
        db.session.get(Service, service_id)
        for service_id in kwargs['services']
    }
    entry = Entry(user_id=user.uuid)
    entry.services.extend(service for service in services if service)
    entry.date = kwargs['date']
    entry.time = kwargs['time']
    db.session.add(entry)
    db.session.commit()
    return entry


@for_entries.route('/entries/', methods=['GET'])
@authenticate(token_auth)
@admin_required
@arguments(EntryFieldSchema(only=['fields']))
@arguments(EntrySortSchema(only=['sort']))
@other_responses({200: 'OK'})
def get_all(fields: dict[str, list[str]],
            sort: dict[str, list[str]]) -> Sequence:
    """Get all entries"""
    mapping = {'fields': EntryFieldSchema, 'sort': EntrySortSchema}
    entries, only = sanitize_query(fields=fields,
                                   filter=None,
                                   sort=sort,
                                   model=Entry,
                                   mapping=mapping)  # type: ignore[arg-type]
    return EntrySchema(many=True, only=only).dump(entries)


@for_entries.route('/entries/<uuid:entry_id>', methods=['GET'])
@authenticate(token_auth)
@response(entry_schema)
@other_responses({
    404: 'Entry not found',
    403: 'You are not allowed to perform this operation'
})
def get_one(entry_id: UUID) -> Entry:
    """Retrieve entry by uuid"""
    user: User = token_auth.current_user()
    entry = get_or_404(Entry, entry_id)
    if not (entry.user == user or user.admin):
        abort(403, 'You are not allowed to perform this operation')
    return entry


@for_entries.route('/entries/<uuid:entry_id>', methods=['PUT'])
@authenticate(token_auth)
@body(update_entry_schema)
@response(entry_schema)
@other_responses({
    404: 'Entry not found',
    403: 'You are not allowed to perform this operation'
})
def update_one(kwargs: dict, entry_id: UUID) -> Entry:
    """Update entry"""
    user: User = token_auth.current_user()
    entry = get_or_404(Entry, entry_id)
    if not (entry.user == user or user.admin):
        abort(403, 'You are not allowed to perform this operation')
    if 'services' in kwargs:
        services = {
            db.session.get(Service, service_id)
            for service_id in kwargs['services']
        }
        entry.services.clear()
        entry.services.extend(service for service in services if service)
    if 'date' in kwargs:
        entry.date = kwargs['date']
    if 'time' in kwargs:
        entry.time = kwargs['time']
    db.session.add(entry)
    db.session.commit()
    return entry


@for_entries.route('/entries/<uuid:entry_id>', methods=['DELETE'])
@authenticate(token_auth)
@other_responses({
    404: 'Entry not found',
    403: 'You are not allowed to perform this operation'
})
def delete_one(entry_id: UUID) -> tuple[str, int]:
    """Delete entry"""
    user: User = token_auth.current_user()
    entry = get_or_404(Entry, entry_id)
    if not (entry.user == user or user.admin):
        abort(403, 'You are not allowed to perform this operation')
    db.session.delete(entry)
    db.session.commit()
    return '', 204


@for_entries.route('/users/<uuid:user_id>/entries', methods=['GET'])
@authenticate(token_auth)
@admin_required
@response(entries_schema)
@other_responses({
    404: 'User not found',
    403: 'You are not allowed to perform this operation'
})
def get_user_entries(user_id: UUID) -> Sequence:
    """Retrieve user's entries"""
    user = get_or_404(User, user_id)
    entries = db.session.scalars(user.entries.select().order_by(Entry.date.desc(), Entry.time.desc())).all()
    return entries  # type: ignore[return-value]


@for_entries.route('/services/<int:service_id>/entries', methods=['GET'])
@authenticate(token_auth)
@admin_required
@response(entries_schema)
@other_responses({
    404: 'Service not found',
    403: 'You are not allowed to perform this operation'
})
def get_service_entries(service_id: int) -> Sequence:
    """Retrieve service's entries"""
    service = get_or_404(Service, service_id)
    entries = db.session.scalars(service.entries.select().order_by(Entry.date.desc(), Entry.time.desc())).all()
    return entries  # type: ignore[return-value]


@for_entries.route('/me/entries', methods=['GET'])
@authenticate(token_auth)
@response(entries_schema)
def my_entries() -> Sequence:
    """Retrieve my entries"""
    user: User = token_auth.current_user()
    entries = db.session.scalars(user.entries.select().order_by(Entry.date.desc(), Entry.time.desc())).all()
    return entries  # type: ignore[return-value]
