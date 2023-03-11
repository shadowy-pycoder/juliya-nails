from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from flask_ckeditor import CKEditorField
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png'])])
    content = CKEditorField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')


class EditPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png'])])
    content = CKEditorField('Content', validators=[DataRequired()])
    submit = SubmitField('Update Post')