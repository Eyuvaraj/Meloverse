from flask import redirect, url_for, render_template, request, Flask, flash
from flask import current_app as app
from .database import db
from .models import User
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(user_id)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method=="POST":
        email = request.form["email"]
        password = request.form["password"]
        remember = True if request.form.get("remember") == "on" else False
        
        user = User.query.filter_by(email=email).first()
        if user is not None and user.password == password:
            if user.role == "admin":
                login_user(user, remember=remember)
                return redirect(url_for("admin_dashboard",user=user.username))
            elif user.role == "user":
                login_user(user, remember=remember)
                return redirect(url_for("user_dashboard",user=user.username))
        elif user is None:
            flash("User does not exist")
            return redirect(url_for("login"))
        else:
            flash("Incorrect password")
            return redirect(url_for("login"))
        
    return render_template("login.html")
        

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":

        username = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        user=User.query.filter_by(email=email).first()
        if user.email == email:
            flash("Email already exists")
            return redirect(url_for("signup"))
        else:
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()

        return redirect(url_for("login"))
    
    return render_template("signup.html")
    
@app.route("/admin/<user>", methods=["GET", "POST"])
@login_required
def admin_dashboard(user):
    return render_template("admin_dashboard.html")

@app.route("/user/<user>", methods=["GET", "POST"])
@login_required
def user_dashboard(user):
    return render_template("user_dashboard.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))