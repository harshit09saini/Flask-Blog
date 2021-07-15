from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField

class NewPost(FlaskForm):
    title = StringField(label="Blog Post Title", validators=[DataRequired()])
    img_url = StringField(label="Image Link", validators=[DataRequired(), URL()])
    content = CKEditorField('Content', validators=[DataRequired()])
    submit = SubmitField(label="Submit Post", validators=[DataRequired()])

class NewComment(FlaskForm):
    comment = CKEditorField('Comment', validators=[DataRequired()])
    submit = SubmitField(label="Add Comment", validators=[DataRequired()])

class RegisterUser(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8, max=32)])
    submit = SubmitField(label="Submit", validators=[DataRequired()])

class LoginUser(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8, max=32)])
    submit = SubmitField(label="Submit", validators=[DataRequired()])
