from uuid import UUID

from apifairy import authenticate, body, response
from flask import jsonify
from flask.wrappers import Response
import sqlalchemy as sa
from sqlalchemy.sql.schema import Sequence

from . import api
from ... import db
from ...models import SocialMedia, get_or_404
from ...schemas import SocilalMediaSchema

social_schema = SocilalMediaSchema()
socials_schema = SocilalMediaSchema(many=True)


@api.route('/socials')
@response(socials_schema)
def get_socials() -> Sequence:
    socials = db.session.scalars(sa.select(SocialMedia)).all()
    return socials  # type: ignore[return-value]


@api.route('/socials/<uuid:social_id>')
@response(social_schema)
def get_social(social_id: UUID) -> SocialMedia:
    social = get_or_404(SocialMedia, social_id)
    return social
