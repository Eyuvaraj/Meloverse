from flask import redirect, url_for, render_template, request, Flask, flash, Blueprint
from flask import current_app as app
from ..database import db
from ..models import Users
from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.session_protection = "strong"

auth = Blueprint("auth", __name__)


@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        remember = True if request.form.get("remember") == "on" else False

        user = Users.query.filter_by(email=email).first()
        if user is not None and user.password == password:
            if user.role == "admin":
                login_user(user, remember=remember)
                return redirect(url_for("admin.admin_dashboard", user=user.username))
            elif user.role == "user":
                login_user(user, remember=remember)
                return redirect(url_for("user.user_dashboard", user=user.username))
        elif user is None:
            flash("User does not exist.")
            return redirect(url_for("auth.login"))
        else:
            flash("Incorrect password, Try again!! or ")
            return redirect(url_for("auth.login"))

    try:
        return redirect(url_for("auth.login"))
    finally:
        return render_template("login.html")


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        user = Users.query.filter_by(email=email).first()
        if user is not None and user.email == email:
            flash("Email already exists")
            return redirect(url_for("auth.signup"))
        else:
            new_user = Users(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth.route("auth/login", methods=["GET", "POST"])
def authlogin():
    return redirect(url_for("auth.login"))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# @login_manager.unauthorized_handler
# def unauthorized():
#     return("Error 404")
