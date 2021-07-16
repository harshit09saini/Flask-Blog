from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from form import NewPost, RegisterUser, LoginUser, NewComment
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, logout_user, current_user, login_required
from functools import wraps
from flask_gravatar import Gravatar
import os
import re

# SQLAlchemy 1.4.x has removed support for the postgres:// URI scheme, which is used by Heroku Postgres
uri = os.getenv("DATABASE_URL")  # or other relevant config var
print(uri)
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
    print(uri)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(uri, "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ckeditor = CKEditor(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False,
                    base_url=None)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)

        return function(*args, **kwargs)

    return wrapper


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    posts = db.relationship('Blog', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='comment_author', lazy=True)


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    img_url = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='blog_post', lazy=True)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    date_commented = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)


# db.drop_all()
db.create_all()

# new_user = User(username="harshitttt", email="123@1233123", password="12312")
# new_blog = Blog(title="hekashfa", img_url="sakfjasfkj", content="ajsfhsjfah", user_id=current_user.id)
# Routes
@app.route('/')
def home():
    all_blogs = Blog.query.all()
    return render_template("index.html", all_blogs=all_blogs, current_user=current_user)


@app.route('/about')
def about():
    return render_template("about.html", current_user=current_user)


@app.route('/contact')
def contact():
    return render_template("contact.html", current_user=current_user)


@app.route('/posts/<int:id>', methods=["GET", "POST"])
def post(id):
    blog_post = Blog.query.get(id)
    form = NewComment()

    if request.method == "POST":
        comment = form.comment.data
        new_comment = Comment(comment=comment, comment_author=current_user, blog_post=blog_post)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(request.url)
    return render_template("post.html", blog_post=blog_post, current_user=current_user, form=form)


# POST ROUTES
@app.route('/add', methods=["GET", "POST"])
@admin_only
def add_post():
    form = NewPost()
    if form.validate_on_submit():
        new_blog = Blog(title=form.title.data,
                        img_url=form.img_url.data,
                        content=form.content.data,
                        author=current_user)
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add.html', form=form, current_user=current_user)


# EDIT POST
@app.route('/edit/<int:id>', methods=["GET", "POST"])
@admin_only
def edit_post(id):
    post_to_edit = Blog.query.get(id)
    edit_form = NewPost(title=post_to_edit.title,
                        img_url=post_to_edit.img_url,
                        content=post_to_edit.content)
    if edit_form.validate_on_submit():
        post_to_edit.title = edit_form.title.data
        post_to_edit.img_url = edit_form.img_url.data
        post_to_edit.content = edit_form.content.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=edit_form, current_user=current_user)


# DELETE POST
@app.route('/delete/<int:id>')
@admin_only
def delete_post(id):
    post_to_delete = Blog.query.get(id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


# ##################### USER AUTHENTICATION ROUTES #################

#  Register
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterUser()

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=request.form.get('email')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        if User.query.filter_by(username=request.form.get('username')).first():
            # User already exists
            flash("Username not Available!")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password=password, method='pbkdf2:sha256:80000', salt_length=8)

        new_user = User(email=email, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html', form=form, current_user=current_user)


# Login
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginUser()

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        # Email exists and password correct
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template('login.html', form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
