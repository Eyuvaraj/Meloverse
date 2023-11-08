from flask import redirect, url_for, render_template, request, Flask, flash, Blueprint
from ..database import db
from ..models import *
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
    if request.method=="POST":
        user_id = request.form.get("user_id")
        grant = request.form.get("grant")
        revoke = request.form.get("revoke")
        user=Users.query.get(user_id)
        if grant=="yes":
            db.session.query(Users).filter_by(id=user_id).update({"role":"admin"})
        elif revoke=="yes":
            db.session.query(Users).filter_by(id=user_id).update({"role":"user"})
        db.session.commit()
    users_=db.session.query(Users, Creator).outerjoin(Creator, Users.id == Creator.creator_id).order_by(Users.role).limit(50).all()
    return render_template("admin/user_mg.html", users=users_)

@admin.route("/admin/<user>/songs_manager", methods=["GET", "POST"])
@login_required
def songs_n_playlist_management(user):
    return render_template("admin/songnplaylists.html")

@admin.route("/admin/<user>/stats", methods=["GET", "POST"])
@login_required
def stats(user):
    return render_template("admin/stats.html")