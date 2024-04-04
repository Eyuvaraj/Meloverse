from flask import render_template, request, flash, Blueprint
from ..database import db
import os
from ..models import *
from sqlalchemy import desc, func
import threading
from datetime import datetime, timedelta
from flask_login import (
    login_required,
    current_user,
)
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


import matplotlib

matplotlib.use("agg")
from matplotlib import pyplot as plt


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
    lastest_record = usage_timeline.query.order_by(
        usage_timeline.timeline_id.desc()
    ).first()
    lastest_record_date = lastest_record.date_time
    trends_start_date = lastest_record_date - timedelta(days=7)
    song_trends = (
        db.session.query(usage_timeline.track_id, func.count().label("count"))
        .filter(usage_timeline.date_time >= trends_start_date)
        .group_by(usage_timeline.track_id)
        .order_by(func.count().desc())
        .limit(3)
        .all()
    )
    album_trends = (
        db.session.query(usage_timeline.album_id, func.count().label("count"))
        .filter(usage_timeline.date_time >= trends_start_date)
        .group_by(usage_timeline.album_id)
        .order_by(func.count().desc())
        .limit(4)
        .all()
    )
    trending_creators = dict()
    trending_songs = dict()
    trending_albums = dict()

    for track_id, count in song_trends:
        track_info = (
            db.session.query(Tracks, Creator)
            .filter(Tracks.track_id == track_id)
            .join(Creator, Creator.creator_id == Tracks.creator_id)
            .first()
        )

        trending_creators[
            track_info.Creator.creator_name
        ] = track_info.Creator.creator_id
        trending_songs[track_info.Tracks.track_name] = count

    for album_id, count in album_trends:
        if album_id != 0:
            album_info = db.session.query(Album).filter_by(album_id=album_id).first()
            trending_albums[album_info.album_name] = count

    return render_template(
        "admin/admin_dashboard.html",
        user_count=user_count,
        admin_count=admin_count,
        creator_count=creator_count,
        album_count=album_count,
        tracks_count=tracks_count,
        singles_count=singles_count,
        top_creators=top_creators,
        trending_creators=trending_creators,
        trending_albums=trending_albums,
        trending_songs=trending_songs,
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
    t = threading.Thread(target=plotter)
    t.start()
    t.join()
    return render_template("admin/stats.html")


@admin.route("/admin/creator/<creator>", methods=["GET", "POST"])
@login_required
def creator_profile(creator):
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
    album_tracks = (
        db.session.query(Album, Tracks)
        .filter(Album.creator_id == creator.creator_id)
        .join(Album, Album.album_id == Tracks.album_id)
        .all()
    )
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
        album_tracks=album_tracks,
    )


@admin.route("/admin/a/<user>/search", methods=["POST", "GET"])
@login_required
def search(user):
    query = request.form.get("search")
    if request.method == "POST":
        print(request.form)
        delete_song = request.form.get("delete_song")
        delete_album = request.form.get("delete_album")
        if delete_song == "yes":
            song_id = request.form.get("song_id")
            song2delete = Tracks.query.filter_by(track_id=song_id).first()
            creator = Creator.query.filter_by(creator_id=song2delete.creator_id).first()
            creator.songs_published -= 1
            if song2delete.album_id == 0:
                creator.no_of_singles -= 1
            elif song2delete.album_id >= 1:
                album = Album.query.filter_by(album_id=song2delete.album_id)
                album.no_of_tracks -= 1
            db.session.delete(song2delete)
            db.session.commit()
        elif delete_album == "yes":
            album_id = request.form.get("album_id")
            album = Album.query.filter_by(album_id=album_id).first()
            tracks = Tracks.query.filter_by(album_id=album_id).all()
            creator = Creator.query.filter_by(creator_id=album.creator_id).first()
            no_of_album_tracks = len(tracks)
            creator.songs_published -= no_of_album_tracks
            for track in tracks:
                db.session.delete(track)
            creator.no_of_albums -= 1
            db.session.delete(album)
            db.session.commit()

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
    plt.xlabel("User Type")
    plt.ylabel("Count")
    plt.bar(x, y)

    filename = "user_cat"
    filepath = os.path.join(assets_path, filename)
    plt.savefig(filepath)
    plt.close()

    album_count = Album.query.count()
    singles_count = Tracks.query.filter_by(album_id=0).count()
    album_tracks_count = Tracks.query.count() - singles_count - 1
    x = ["Albums", "Singles", "Album Tracks"]
    y = [album_count, singles_count, album_tracks_count]
    plt.bar(x, y)
    plt.xlabel("Music Catalogue")
    plt.ylabel("Count")

    filename = "song_cat"
    filepath = os.path.join(assets_path, filename)
    plt.savefig(filepath)
    plt.close()

    genre_types_count = (
        db.session.query(Tracks.genre, func.count(Tracks.genre))
        .group_by(Tracks.genre)
        .all()
    )

    genre_types, count = zip(*genre_types_count)
    plt.bar(genre_types, count)
    plt.xlabel("Genre")
    plt.ylabel("Count")
    filename = "genre_count"
    filepath = os.path.join(assets_path, filename)
    plt.savefig(filepath)
    plt.close()

    join_dates = db.session.query(Users.date_joined).all()

    user_count_by_date = {}
    cumulative_users = []
    current_cumulative = 0  # Keep track of the cumulative count

    for join_date in join_dates:
        date_str = join_date
        user_count_by_date[date_str] = user_count_by_date.get(date_str, 0) + 1
        current_cumulative += 1  # Increment cumulative count
        cumulative_users.append(current_cumulative)

    dates, user_counts = zip(*sorted(user_count_by_date.items()))
    cumulative_users = tuple(cumulative_users)  # Convert to tuple
    plt.figure(figsize=(12, 6))
    plt.plot(cumulative_users, dates)
    plt.ylabel("Join Date")
    plt.xlabel("Number of Users Joined")
    filename = "users_gained"
    filepath = os.path.join(assets_path, filename)
    plt.savefig(filepath)
    plt.close()

    creators = Creator.query.all()
    creator_name, followers = [], []
    for creator in creators:
        creator_name.append(creator.creator_name)
        followers.append(creator.followers)
    plt.figure(figsize=(12, 6))
    plt.bar(creator_name, followers)
    plt.xlabel("Creator")
    plt.ylabel("Followers")
    filename = "creator_followers"
    filepath = os.path.join(assets_path, filename)
    plt.savefig(filepath)
    plt.close()
    return
