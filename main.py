from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreateTodoForm, RegisterForm, LoginForm, ContactForm
from flask_gravatar import Gravatar
from functools import wraps
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import smtplib
import os
from dotenv import load_dotenv
from _datetime import datetime
import threading
from bs4 import BeautifulSoup


new_day = False
load_dotenv()
PASSWORD = os.getenv('CE_PW')
MY_EMAIL = os.getenv('MY_EMAIL')
SMTP_SERVER = os.getenv('SMTP_SERVER')
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CONFIGURE TABLES
# Create the User Table
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    # Link 'todos' relationship with TODO_List.
    todos = relationship('TODO_List', back_populates='user')


# Create TODO_List Table
class TODO_List(db.Model):
    __tablename__ = "todo_list"
    id = db.Column(db.Integer, primary_key=True)
    project = db.Column(db.String(250), unique=False, nullable=False)
    title = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(250), nullable=False)
    # ForeignKey need for child.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 'user' point to a User object.
    user = relationship("User", back_populates="todos")
    
    
db.create_all()


# Enable login manager
login_manager = LoginManager()
login_manager.init_app(app)


# Initialize Gravatar
gravatar = Gravatar(
    app, size=100, rating='g', default='retro',
    force_default=False, force_lower=False,
    use_ssl=False, base_url=None)


# Function to send email
def send_mail(name, email, phone, message):
    with smtplib.SMTP(SMTP_SERVER) as connection:
        connection.starttls()
        connection.login(user=MY_EMAIL, password=PASSWORD)
        new_message = f"Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage:\n{message}"
        message = f"From:{MY_EMAIL}\nSubject: Message from {name}\n\n{new_message}\n"
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=MY_EMAIL,
            msg=message)


# Send notification
def send_notification(todo):
    with smtplib.SMTP(SMTP_SERVER) as connection:
        connection.starttls()
        connection.login(user=MY_EMAIL, password=PASSWORD)
        todo_body = BeautifulSoup(todo.body, "html.parser").text
        new_message = f"Dear {todo.user.name},\n\nYou have a TODO item deal on {todo.date}\n\n" \
                      f"Project: {todo.project}\n\n" \
                      f"Title: {todo.title}\n\n" \
                      f"Items:\n{todo_body}\n\n\n" \
                      f"From ToDoo"
        message = f"From:{MY_EMAIL}\nSubject: ToDooo Notification: {todo.project}\n\n{new_message}\n"
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=todo.user.email,
            msg=message)

@login_manager.user_loader
def load_user(user_email):
    return User.query.get(int(user_email))


def admin_only(fn):
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        if not current_user.is_anonymous:
            if current_user.id == 1:
                return fn(*args, **kwargs)
        return abort(403)
    return decorated_function
    

@app.route('/')
def get_all_todo():
    if current_user.is_authenticated:
        all_todo = TODO_List.query.filter_by(user_id=current_user.id).all()
        return render_template("index.html", all_todo=all_todo, name=current_user.name)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=request.form["email"]).first():
            flash("You have already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        hash_salted_password = generate_password_hash(
            request.form["password"],
            method='pbkdf2:sha256',
            salt_length=8
            )
        new_user = User(
            name=request.form['name'],
            email=request.form['email'],
            password=hash_salted_password,
            )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_todo'))
    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        # db.email is set to have unique email
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('That email does not exist, please try again.')
            return redirect(url_for('register'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again')
        else:
            # login_user will pass .id to user_loader
            login_user(user)
            return redirect(url_for('get_all_todo'))
    return render_template("login.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/todo_list/<int:todo_id>", methods=['GET', 'POST'])
@login_required
def show_todo(todo_id):
    # form = CommentForm()
    requested_todo = TODO_List.query.get(todo_id)
    return render_template("todo.html", todo=requested_todo)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        data = request.form
        send_mail(data['name'], data['email'], data['phone'], data['message'])
        return render_template('contact.html', form=form, msg_sent=True)
    return render_template('contact.html', form=form, msg_sent=False)


@app.route("/new-todo", methods=['GET', 'POST'])
@login_required
def add_new_todo():
    form = CreateTodoForm()
    if form.validate_on_submit():
        new_todo = TODO_List(
            project=form.project.data,
            title=form.title.data,
            body=form.body.data,
            date=form.date.data.strftime("%B %d, %Y"),
            user_id=current_user.id,
        )
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for("get_all_todo"))
    return render_template("make-todo.html", form=form)


@app.route("/edit-todo/<int:todo_id>", methods=['GET', 'POST'])
@login_required
def edit_todo(todo_id):
    todo = TODO_List.query.get(todo_id)
    edit_form = CreateTodoForm(
        project=todo.project,
        title=todo.title,
        body=todo.body,
        date=datetime.strptime(todo.date, '%B %d, %Y'),
        user_id=current_user.id,
    )
    if edit_form.validate_on_submit():
        todo.project = edit_form.project.data
        todo.title = edit_form.title.data
        todo.body = edit_form.body.data
        todo.date = edit_form.date.data.strftime("%B %d, %Y")
        db.session.commit()
        return redirect(url_for("get_all_todo"))
    return render_template("make-todo.html", form=edit_form)


@app.route("/delete/<int:todo_id>", methods=['GET', 'POST'])
@login_required
def delete_todo(todo_id):
    todo_to_delete = TODO_List.query.get(todo_id)
    db.session.delete(todo_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_todo'))


# Create an hourly timer.
def one_hour_timer():
    global new_day
    # Check when the world turn to next day.
    today = datetime.utcnow()
    current_hour = today.hour
    all_todo = TODO_List.query.all()
    for todo in all_todo:
        todo_date = datetime.strptime(todo.date, '%B %d, %Y')
        if todo_date <= today:
            send_notification(todo)
    if current_hour == 0:
        # 'new_day' only check todo_list once per day.
        if not new_day:
            new_day = True
            all_todo = TODO_List.query.all()
            for todo in all_todo:
                todo_date = datetime.strptime(todo.date, '%B %d, %Y')
                if todo_date <= today:
                    send_notification(todo)
    else:
        new_day = False

        
t = threading.Timer(3600, one_hour_timer)
t.start()


if __name__ == "__main__":
    app.run(debug=True)
