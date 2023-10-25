from flask import redirect, url_for, render_template, request, Flask, flash, Blueprint
from flask import current_app as app
from ..database import db
from ..models import Users, Creator
from flask_login import login_required, current_user
from application.app_controllers import auth

user=Blueprint('user',__name__)

@user.route("/user/<user>/home", methods=["GET", "POST"])
@login_required
def user_dashboard(user):
    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    return render_template("user/user_dashboard.html", creator_signup_status=creator)

@user.route("user/<user>/creator_signup", methods=["GET", "POST"])
@login_required
def creator_signup(user):
    if request.method=="POST":
        new_creator = Creator(creator_id=current_user.id, creator_name=current_user.username, creator_email=current_user.email)
        db.session.add(new_creator)
        db.session.commit()
        return redirect(url_for('user.user_dashboard', user=user))
    return render_template("user/creator_signup.html")

@user.route("user/<user>/favorites", methods=["GET", "POST"])
@login_required
def favorites(user):
    return render_template("user/favorites.html")

@user.route("user/<user>/my_playlists", methods=["GET", "POST"])
@login_required
def user_playlists(user):
    return render_template("user/user_playlists.html")

@user.route("user/<user>/discover", methods=["GET", "POST"])
@login_required
def discover(user):
    return render_template("user/discover.html")

@user.route("creator_center/<user>/", methods=["GET", "POST"])
@login_required
def creator_dashboard(user):
    return render_template("creator/creator_center.html")