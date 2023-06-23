import sys

from sqlalchemy.sql import func

from website import create_app, db
from website.models import User, SocialMedia


def create_db(config: str, username: str, email: str, password: str) -> None:
    app = create_app(config)

    db.init_app(app)
    db.Model.metadata.drop_all(db.engine)
    db.Model.metadata.create_all(db.engine)
    db.session.commit()

    user = User(
        username=username,
        email=email,
        password=password,
        confirmed=True,
        confirmed_on=func.now(),
        admin=True,
    )
    db.session.add(user)
    db.session.commit()
    socials = SocialMedia(user_id=user.uuid)
    db.session.add(socials)
    db.session.commit()


def main(args: list[str]) -> None:
    if len(args) != 5:
        raise SystemExit(f'Usage: {args[0]} config username email password')
    create_db(args[1], args[2], args[3], args[4])


if __name__ == '__main__':
    main(sys.argv)
