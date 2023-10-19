from flask import Flask, request
from flask import render_template
from flask import current_app as app

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("base.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    return render_template("signup.html")