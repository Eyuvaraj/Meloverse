from flask import redirect, url_for, render_template, request, Flask, flash, Blueprint
from flask import current_app as app
from ..database import db
from ..models import Users, Creator, Announcement, Announcement_stats
from flask_login import login_required, current_user
from application.app_controllers import auth
from datetime import datetime

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
    if request.method=="POST":
        user=current_user.id
        reaction=request.form.get('reaction')
        announcement_id=request.form.get('announcement_id')
        announcement=Announcement.query.filter_by(announcement_id=announcement_id).first()
        already_liked=Announcement_stats.query.filter_by(announcement_id=announcement_id, user_id=user).first()
        
        if already_liked:
            if reaction=="like" and already_liked.value != 1:
                already_liked.value=1
                announcement.likes+=1
                announcement.dislikes-=1
            elif reaction=="dislike" and already_liked.value != -1:
                already_liked.value=-1
                announcement.dislikes+=1
                announcement.likes-=1
        else:
            if reaction=="like":
                new_announcement_stat=Announcement_stats(announcement_id=announcement_id, user_id=user, value=1)
                announcement.likes+=1
            elif reaction=="dislike":
                new_announcement_stat=Announcement_stats(announcement_id=announcement_id, user_id=user, value=-1)
                announcement.dislikes+=1
            db.session.add(new_announcement_stat)

        db.session.commit()
    announcements=Announcement.query.order_by(Announcement.date.desc()).limit(10).all()
    return render_template("user/discover.html", announcements=announcements)

@user.route("creator_center/<user>/", methods=["GET", "POST"])
@login_required
def creator_dashboard(user):
    return render_template("creator/creator_center.html")

@user.route("creator_center/<user>/new", methods=["GET", "POST"])
@login_required
def new(user):
    return render_template("creator/new.html")

@user.route("creator_center/<user>/profile", methods=["GET", "POST"])
@login_required
def profile(user):
    if request.form.get("edit_profile")=="True":
        return redirect(url_for("user.edit_profile", user=current_user.username))
    creator=Creator.query.filter_by(creator_id=current_user.id).first()
    return render_template("creator/profile.html", bio=creator.bio)

@user.route("creator_center/<user>/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile(user):
    if request.method=="POST":
        name=request.form["name"]
        bio=request.form["bio"]
        user = Users.query.filter_by(id=current_user.id).first()
        creator = Creator.query.filter_by(creator_id=current_user.id).first()
        if user and creator:
            if name != "":
                user.username=name
            elif bio != "":
                creator.bio=bio
            db.session.commit()
        return redirect(url_for("user.profile", user=current_user.username))
    return render_template("creator/edit_profile.html")

@user.route("creator_center/<user>/announcement", methods=["GET", "POST"])
@login_required
def announcement(user):
    if request.method=="POST":
        announcement = request.form.get('announcement')
        if announcement != "":
            creator = current_user.username
            heading = request.form.get('heading')
            link = request.form.get('link')
            date = datetime.now()
            new_annoucement=Announcement(announcement=announcement, date=date, creator=creator, heading=heading, link=link)
            db.session.add(new_annoucement)
            db.session.commit()
            flash("Annoucement Posted 🎊")
    return render_template("creator/announcement.html", user=current_user.username)