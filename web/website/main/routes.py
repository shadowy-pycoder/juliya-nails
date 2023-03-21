from flask import render_template, Blueprint, flash, redirect, url_for
from flask_login import current_user
from .forms import PostForm, EditPostForm
from .. models import Post, SocialMedia
from .. utils import admin_required, save_image, delete_image
from .. import db

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    posts = Post.query.order_by(Post.posted_on.desc()).all()
    return render_template('home.html', title='Home', posts=posts)


@main.route("/about")
def about():
    return render_template('about.html', title='About')


def page_not_found(e):
    return render_template('404.html', title='Page Not Found'), 404


@main.route("/create-post", methods=['GET', 'POST'])
@admin_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        image = save_image(form.image) if form.image.data else None
        post = Post(title=form.title.data, image=image, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_post.html', title='Create Post', legend='Create Post', form=form)


@main.route("/edit-post/<post_id>", methods=['GET', 'POST'])
@admin_required
def edit_post(post_id):
    form = EditPostForm()
    post: Post = Post.query.get_or_404(post_id)
    if form.validate_on_submit():
        image = save_image(form.image) if form.image.data else post.image
        post.title = form.title.data
        post.image = image
        post.content = form.content.data
        db.session.add(post)
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('main.home'))
    form.title.data = post.title
    form.content.data = post.content
    return render_template('edit_post.html', title='Edit Post', legend='Edit Post', form=form)


@main.route("/delete-post/<post_id>", methods=['GET', 'POST'])
@admin_required
def delete_post(post_id):
    post: Post = Post.query.get_or_404(post_id)
    if post.image is not None:
        try:
            delete_image(post.image)
        except FileNotFoundError:
            pass
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('main.home'))
