from flask import redirect, url_for, render_template, request, Flask, flash, Blueprint
from flask import current_app as app
from ..database import db
from ..models import Users
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from application.app_controllers import auth

admin=Blueprint('admin',__name__)

@admin.route("/admin/<user>/home", methods=["GET", "POST"])
@login_required
def admin_dashboard(user):
    return render_template("admin/admin_dashboard.html")

@admin.route("/admin/<user>/user_manager", methods=["GET", "POST"])
@login_required
def user_management(user):
    return render_template("admin/user_mg.html")

@admin.route("/admin/<user>/songs_manager", methods=["GET", "POST"])
@login_required
def songs_n_playlist_management(user):
    return render_template("admin/songnplaylists.html")

@admin.route("/admin/<user>/stats", methods=["GET", "POST"])
@login_required
def stats(user):
    return render_template("admin/stats.html")