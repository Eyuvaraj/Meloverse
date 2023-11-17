from flask import redirect, url_for, render_template, request, Flask, flash, Blueprint
from flask import current_app as app
from .database import db


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")
