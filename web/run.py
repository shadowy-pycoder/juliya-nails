from website import create_app, db


app = create_app('development')


if __name__ == '__main__':

    # app.app_context().push()
    db.Model.metadata.create_all(db.engine)
    app.run()
