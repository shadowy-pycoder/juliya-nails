from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png'])])
    content = CKEditorField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')


class EditPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    image = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png'])])
    delete_image = BooleanField('Delete previous image file')
    content = CKEditorField('Content', validators=[DataRequired()])
    submit = SubmitField('Update Post')
