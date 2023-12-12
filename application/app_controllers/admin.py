from flask import redirect, url_for, render_template, request, Flask, flash, Blueprint
from ..database import db
import os
from ..models import *
from sqlalchemy import desc
from datetime import datetime
from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from application.app_controllers import auth
from sqlalchemy.orm import aliased

admin = Blueprint("admin", __name__)


def search_result(query):
    creators = Creator.query.filter(Creator.creator_name.ilike(f"%{query}%")).all()
    albums = (
        db.session.query(Album, Tracks, Creator)
        .filter(Album.album_name.ilike(f"%{query}%"))
        .join(Album, Album.album_id == Tracks.album_id)
        .join(Creator, Album.creator_id == Creator.creator_id)
        .all()
    )
    songs = (
        db.session.query(Tracks, Creator, Album)
        .filter(Tracks.track_name.ilike(f"%{query}%"))
        .join(Creator, Tracks.creator_id == Creator.creator_id)
        .outerjoin(Album, Album.album_id == Tracks.album_id)
        .all()
    )

    genre = (
        db.session.query(Tracks, Creator, Album)
        .filter(Tracks.genre.ilike(f"%{query}%"))
        .join(Creator, Tracks.creator_id == Creator.creator_id)
        .outerjoin(Album, Tracks.album_id == Album.album_id)
        .all()
    )

    return creators, albums, songs, genre


from matplotlib import pyplot as plt
import numpy


def get_data_vis_assets_path():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(current_directory, "..", "..", "static")
    data_vis_dir = os.path.join(static_dir, "data_vis_assets")
    return data_vis_dir


@admin.route("/admin/<user>/home", methods=["GET", "POST"])
@login_required
def admin_dashboard(user):
    user_count = Users.query.count()
    admin_count = Users.query.filter_by(role="admin").count()
    creator_count = Creator.query.count()
    album_count = Album.query.count()
    tracks_count = Tracks.query.count()
    singles_count = Tracks.query.filter_by(album_id="0").count()
    top_creators = Creator.query.order_by(desc(Creator.followers)).limit(3).all()
    treading_creators = Creator.query.count()
    return render_template(
        "admin/admin_dashboard.html",
        user_count=user_count,
        admin_count=admin_count,
        creator_count=creator_count,
        album_count=album_count,
        tracks_count=tracks_count,
        singles_count=singles_count,
        top_creators=top_creators,
    )


@admin.route("/admin/<user>/user_manager", methods=["GET", "POST"])
@login_required
def user_management(user):
    if request.method == "POST":
        user_id = request.form.get("user_id")
        grant = request.form.get("grant")
        revoke = request.form.get("revoke")
        user = Users.query.get(user_id)
        if grant == "yes":
            db.session.query(Users).filter_by(id=user_id).update({"role": "admin"})
        elif revoke == "yes":
            db.session.query(Users).filter_by(id=user_id).update({"role": "user"})
        db.session.commit()
    admin_and_creators = (
        db.session.query(Users, Creator)
        .outerjoin(Creator, Users.id == Creator.creator_id)
        .filter(Users.role == "admin")
        .all()
    )
    creators_only = (
        db.session.query(Users, Creator)
        .join(Creator, Users.id == Creator.creator_id)
        .filter(Users.role == "user")
        .all()
    )
    users_ = admin_and_creators + creators_only
    return render_template("admin/user_mg.html", users=users_)


@admin.route("/admin/<user>/create_alerts", methods=["GET", "POST"])
@login_required
def alert(user):
    if request.method == "POST":
        alert_text = request.form.get("alert")
        link = request.form.get("link")
        new_alert = Alerts(
            alert=alert_text,
            link=link,
            date=datetime.now(),
            user_id=current_user.id,
        )
        db.session.add(new_alert)
        db.session.commit()
        flash("Alert Posted👍")
    return render_template("admin/alerts.html")


@admin.route("/admin/<user>/stats", methods=["GET"])
@login_required
def stats(user):
    plotter()
    return render_template("admin/stats.html")


@admin.route("/admin/<user>/creator/<creator>", methods=["GET", "POST"])
@login_required
def creator_profile(user, creator):
    creator = Creator.query.get(creator)
    if request.method == "POST":
        song_id = request.form.get("song_id")
        song = Tracks.query.filter_by(track_id=song_id).first()
        if song != None and request.form.get("delete_song") == "yes":
            db.session.delete(song)
            creator.songs_published -= 1
            if song.album_id == 0:
                creator.no_of_singles -= 1
            else:
                album = Album.query.filter_by(album_id=song.album_id).first()
                album.no_of_tracks -= 1
        db.session.commit()

        album_id = request.form.get("album_id")
        album = Album.query.filter_by(album_id=album_id).first()
        if album != None and request.form.get("delete_album") == "yes":
            album_tracks = Tracks.query.filter_by(album_id=album_id).all()
            no_of_album_tracks = len(album_tracks)
            creator.songs_published -= no_of_album_tracks
            for tracks in album_tracks:
                db.session.delete(tracks)
            db.session.delete(album)
            creator.no_of_albums -= 1
        db.session.commit()

        print(request.form)

    singles = Tracks.query.filter_by(creator_id=creator.creator_id, album_id=0).all()

    songs = (
        db.session.query(Tracks, Album.album_name)
        .join(Album, Tracks.album_id == Album.album_id)
        .filter(Tracks.creator_id == creator.creator_id)
        .all()
    )

    tracks_alias = aliased(Tracks)

    album_obj = (
        db.session.query(
            Album,
            db.func.sum(tracks_alias.plays).label("total_plays"),
            db.func.sum(tracks_alias.likes).label("total_likes"),
            db.func.sum(tracks_alias.dislikes).label("total_dislikes"),
        )
        .join(tracks_alias, Album.album_id == tracks_alias.album_id)
        .join(Creator, Album.creator_id == Creator.creator_id)
        .filter(Creator.creator_id == creator.creator_id)
        .group_by(
            Album.album_id,
            Album.album_name,
            Album.release_year,
            Album.genre,
            Album.description,
            Album.no_of_tracks,
        )
        .all()
    )

    return render_template(
        "admin/creator_profile.html",
        creator=creator,
        albums_obj=album_obj,
        singles=singles,
        songs=songs,
    )


@admin.route("/admin/a/<user>/search", methods=["POST", "GET"])
@login_required
def search(user):
    if request.method == "POST":
        print(request.form)
    query = request.form.get("search")
    creators, albums, songs, genre = search_result(query)
    return render_template(
        "admin/search.html",
        creators=creators,
        albums=albums,
        tracks=songs,
        query=query,
        genre=genre,
    )


def plotter():
    assets_path = get_data_vis_assets_path()

    user_count = Users.query.count()
    admin_count = Users.query.filter_by(role="admin").count()
    creator_count = Creator.query.count()
    x = ["users", "admin", "creators"]
    y = [user_count, admin_count, creator_count]
    plt.bar(x, y)

    filename = "user_cat"
    filepath = os.path.join(assets_path, filename)
    plt.savefig(filepath)
    plt.close()

    album_count = Album.query.count()
    singles_count = Tracks.query.filter_by(album_id=0).count()
    album_tracks_count = Tracks.query.count() - singles_count - 1
    x = ["Albums", "Singles", "Album Songs"]
    y = [album_count, singles_count, album_tracks_count]
    plt.bar(x, y)

    filename = "song_cat"
    filepath = os.path.join(assets_path, filename)
    plt.savefig(filepath)
    plt.close()
