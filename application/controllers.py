from flask import redirect, url_for, render_template, request, Flask
from flask import current_app as app
from .database import db
from .models import User

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method=="GET":
        return render_template("login.html")
    if request.method=="POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, password=password).first()

        if user is None:
            return redirect(url_for("login"))
        else:
            return redirect(url_for("admin_dashboard"))
        

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    if request.method == "POST":

        username = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("index"))
    
@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route("/user", methods=["GET", "POST"])
def user_dashboard():
    return render_template("user_dashboard.html")