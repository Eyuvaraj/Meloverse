from flask import redirect, url_for, render_template, request, Flask, flash, Blueprint
from flask import current_app as app
from ..database import db
from ..models import *
from flask_login import login_required, current_user
from application.app_controllers import auth
from datetime import datetime
from sqlalchemy import text

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
    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    return render_template("user/creator_signup.html", creator_signup_status=creator)

@user.route("user/<user>/favorites", methods=["GET", "POST"])
@login_required
def favorites(user):
    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    return render_template("user/favorites.html", creator_signup_status=creator)

@user.route("user/<user>/my_playlists", methods=["GET", "POST"])
@login_required
def user_playlists(user):
    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    return render_template("user/user_playlists.html", creator_signup_status=creator)

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
    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    return render_template("user/discover.html", announcements=announcements, creator_signup_status=creator)

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
            if bio != "":
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


@user.route("creator_center/<user>/new_single", methods=["GET", "POST"])
@login_required
def new_single(user):
    if request.method=="POST":
        song_name=request.form.get('song_name')
        artists=request.form.get('artists')
        song_link=request.form.get('song_link')
        genre=request.form.get('genre')
        lyrics=request.form.get('lyrics')
        duration=request.form.get('duration')
        creator_id=current_user.id
        date=datetime.now().date()
        new_song=Tracks(track_name=song_name, artists=artists, creator_id=creator_id,date_created=date, track_link=song_link, genre=genre, lyrics=lyrics, duration=duration)
        db.session.add(new_song)
        no_of_singles_update=text('update creator set no_of_singles=no_of_singles+1 where creator_id= :id')
        db.session.execute(no_of_singles_update,{"id": creator_id})
        no_of_songs_update=text('update creator set songs_published=songs_published+1 where creator_id= :id')
        db.session.execute(no_of_songs_update,{"id": creator_id})
        db.session.commit()
        return render_template("creator/success.html", user=current_user.username, song_or_album="song")
    return render_template("creator/new_single.html", user=current_user)


@user.route("creator_center/<user>/<album>/add_track", methods=["GET", "POST"])
@login_required
def add_track(user, album):
    album=Album.query.filter_by(creator_id=current_user.id, album_name=album).first()
    if request.method=="POST":
        song_name=request.form.get('song_name')
        artists=request.form.get('artists')
        song_link=request.form.get('song_link')
        genre=album.genre
        lyrics=request.form.get('lyrics')
        duration=request.form.get('duration')
        creator_id=album.creator_id
        date=datetime.now().date()
        new_track=Tracks(track_name=song_name, artists=artists, creator_id=creator_id, date_created=date, track_link=song_link, genre=genre, lyrics=lyrics, duration=duration, album_id=album.album_id)
        db.session.add(new_track)
        no_of_album_tracks_update=text('update album set no_of_tracks=no_of_tracks+1 where creator_id= :id and album_id= :album_id')
        db.session.execute(no_of_album_tracks_update,{"id": creator_id, "album_id": album.album_id})
        no_of_songs_update=text('update creator set songs_published=songs_published+1 where creator_id= :id')
        db.session.execute(no_of_songs_update,{"id": creator_id})
        db.session.commit()
        add_track=request.form.get('add_track')
        publish=request.form.get('publish')
        if add_track=='True':
            return render_template("creator/add_track.html", user=current_user.username, album=album)
        elif publish=='True':
            return render_template("creator/success.html", user=current_user.username, song_or_album="album")
    return render_template("creator/add_track.html", user=current_user.username, album=album)


@user.route("creator_center/<user>/new_album", methods=["GET", "POST"])
@login_required
def new_album(user):
    if request.method=="POST":
        album_name=request.form.get('album_name')
        year=datetime.now().year
        genre=request.form.get('genre')
        description=request.form.get('album_description')
        creator_id=current_user.id
        new_album=Album(album_name=album_name, release_year=year, genre=genre, description=description, creator_id=creator_id)
        db.session.add(new_album)
        no_of_albums_update=text('update creator set no_of_albums=no_of_albums+1 where creator_id= :id')
        db.session.execute(no_of_albums_update, {"id": creator_id})
        db.session.commit()
        add_track=request.form.get('add_track')
        if add_track=='True':
            return redirect(url_for("user.add_track", user=current_user.username, album=album_name))
    return render_template("creator/new_album.html", user=current_user.username)