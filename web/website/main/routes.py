from flask import render_template, Blueprint

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    return render_template('home.html')


@main.route("/about")
def about():
    return render_template('about.html', title='About')


def page_not_found(e):
    return render_template('404.html'), 404
