import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, InputRequired
from flask_ckeditor import CKEditorField


# WTForm
class CreateTodoForm(FlaskForm):
    project = StringField("Project Name", validators=[DataRequired()])
    title = StringField("Todo Title", validators=[DataRequired()])
    body = CKEditorField("Todo Items", validators=[DataRequired()])
    date = DateField("Dateline", validators=[DataRequired()], default=datetime.datetime.today())
    submit = SubmitField("Submit Todo")


class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")
    
    
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    # email = StringField('Email', validators=[InputRequired()])
    email = EmailField('Email', validators=[InputRequired(), Email(allow_empty_local=False)])
    phone = StringField('Phone', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()], render_kw={'rows': 10})
    submit = SubmitField('SEND')
    