from flask import render_template, Blueprint, flash, redirect, url_for
from flask_login import current_user
from .forms import PostForm
from .. models import Post
from .. utils import admin_required, save_post_picture
from .. import db

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    posts = Post.query.order_by(Post.posted_on.desc()).all()
    return render_template('home.html', posts=posts)


@main.route("/about")
@admin_required
def about():
    return render_template('about.html', title='About')


def page_not_found(e):
    return render_template('404.html'), 404

@main.route("/create_post", methods=['GET', 'POST'])
@admin_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        image = save_post_picture(form.image)
        post = Post(title=form.title.data, image=image, content=form.content.data, author=current_user)
        print(post)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_post.html', form=form) 
