from website import create_app, db

app = create_app()

if __name__ == '__main__':
    app.app_context().push()
    db.create_all()
    app.run()
