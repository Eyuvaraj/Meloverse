from flask import redirect, url_for, render_template, request, Flask, flash, Blueprint
from flask import current_app as app
from ..database import db
from ..models import Users
from flask_login import login_required, current_user
from application.app_controllers import auth

user=Blueprint('user',__name__)

@user.route("/user/<user>", methods=["GET", "POST"])
@login_required
def user_dashboard(user):
    return render_template("user/user_dashboard.html")

@user.route("/creator_center/<user>", methods=["GET", "POST"])
@login_required
def creator_dashboard(user):
    return render_template("creator/creator_center.html")