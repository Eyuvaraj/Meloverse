from flask import (
    redirect,
    url_for,
    render_template,
    request,
    Flask,
    flash,
    Blueprint,
    jsonify,
)

from flask import current_app as app
from ..database import db
from ..models import *
from flask_login import login_required, current_user
from application.app_controllers import auth
from datetime import datetime
from sqlalchemy import text, func
from sqlalchemy.orm import aliased
import random

user = Blueprint("user", __name__)


def get_album(album_id):
    album = (
        db.session.query(Album, Tracks, Creator)
        .filter(Album.album_id == album_id)
        .join(Album, Album.album_id == Tracks.album_id)
        .join(Creator, Creator.creator_id == Album.creator_id)
        .all()
    )
    return album


def get_single(single_id):
    single = (
        db.session.query(Tracks, Creator)
        .filter(Tracks.album_id == 0, Tracks.track_id == single_id)
        .join(Creator, Tracks.creator_id == Creator.creator_id)
        .first()
    )
    return single


def search_query(query):
    creators = Creator.query.filter(Creator.creator_name.ilike(f"%{query}%")).all()
    albums = (
        db.session.query(Album, Tracks, Creator)
        .filter(Album.album_name.ilike(f"%{query}%"))
        .join(Tracks, Album.album_id == Tracks.album_id)
        .join(Creator, Album.creator_id == Creator.creator_id)
        .all()
    )
    tracks = (
        db.session.query(Tracks, Creator, Album)
        .filter(Tracks.track_name.ilike(f"%{query}%"))
        .join(Creator, Tracks.creator_id == Creator.creator_id)
        .outerjoin(Album, Tracks.album_id == Album.album_id)
        .all()
    )
    genre = (
        db.session.query(Tracks, Creator, Album)
        .filter(Tracks.genre.ilike(f"%{query}%"))
        .join(Creator, Tracks.creator_id == Creator.creator_id)
        .outerjoin(Album, Tracks.album_id == Album.album_id)
        .all()
    )
    return creators, albums, tracks, genre


@user.route("/meloverse/u/<user>/home", methods=["GET", "POST"])
@login_required
def user_dashboard(user):
    alert = Alerts.query.order_by(Alerts.alert_id.desc()).limit(1).first()
    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    album_count = Album.query.count()
    track_count = abs(Tracks.query.count())
    singles = []
    while len(singles) <= 5:
        random_tracks_no = random.randint(2, track_count)
        single = get_single(random_tracks_no)
        if single != None and single not in singles:
            singles.append(single)

    albums = []
    while len(albums) <= 3:
        random_album_no = random.randint(1, album_count)
        temp = get_album(random_album_no)
        if temp != None and temp not in albums:
            albums.append(temp)

    album_liked = []
    for item in albums:
        for x, y, z in item:
            album_id = x.album_id
            user_id = current_user.id
            item = Album_likes_stats.query.filter(
                Album_likes_stats.user_id == user_id,
                Album_likes_stats.album_id == album_id,
            ).first()
            if item != None:
                album_liked.append(album_id)

    singles_liked, singles_disliked = [], []
    for track, creator in singles:
        track_id = track.track_id
        user_id = current_user.id
        item = Track_likes_stats.query.filter(
            Track_likes_stats.user_id == user_id,
            Track_likes_stats.track_id == track_id,
        ).first()
        if item != None and item.value == 1:
            singles_liked.append(track_id)
        elif item != None and item.value == -1:
            singles_disliked.append(track_id)

    return render_template(
        "user/user_dashboard.html",
        creator_signup_status=creator,
        alert=alert,
        singles=singles,
        albums=albums,
        liked_albums=set(album_liked),
        liked_singles=set(singles_liked),
        disliked_singles=set(singles_disliked),
    )


@user.route("/meloverse/u/<user>/creator_signup", methods=["GET", "POST"])
@login_required
def creator_signup(user):
    if request.method == "POST":
        new_creator = Creator(
            creator_id=current_user.id,
            creator_name=current_user.username,
            creator_email=current_user.email,
        )
        db.session.add(new_creator)
        db.session.commit()
        return redirect(url_for("user.user_dashboard", user=user))
    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    return render_template("user/creator_signup.html", creator_signup_status=creator)


@user.route("/meloverse/u/<user>/favorites", methods=["GET", "POST"])
@login_required
def favorites(user):
    if request.method == "POST":
        reaction = request.form.get("reaction")
        if reaction == "unfollow":
            artist_id = request.form.get("artist_id")
            delete_record = whois_Followeing_who.query.filter(
                whois_Followeing_who.fan_id == current_user.id,
                whois_Followeing_who.fan_of == artist_id,
            ).first()
            db.session.delete(delete_record)
            creator = Creator.query.filter_by(creator_id=artist_id).first()
            creator.followers -= 1
            db.session.commit()

        elif reaction == "remove_playlist":
            playlist_id = request.form.get("playlist_id")
            delete_record = Playlist_likes_stats.query.filter(
                Playlist_likes_stats.user_id == current_user.id,
                Playlist_likes_stats.playlist_id == playlist_id,
            ).first()
            db.session.delete(delete_record)
            db.session.commit()

        return redirect(url_for("user.favorites", user=current_user.id))

    creator = Creator.query.filter_by(creator_id=current_user.id).first()

    artists_followed_id = whois_Followeing_who.query.filter_by(
        fan_id=current_user.id
    ).all()

    artists_followed = []
    for i in artists_followed_id:
        artist = Creator.query.filter_by(creator_id=i.fan_of).first()
        artists_followed.append(artist)

    fav_playlist_id = Playlist_likes_stats.query.filter_by(
        user_id=current_user.id
    ).all()

    fav_playlists, fav_playlist_tracks = [], []
    for i in fav_playlist_id:
        playlist = Playlist.query.filter_by(playlist_id=i.playlist_id).first()
        fav_playlists.append(playlist)
        fav_playlist_track = (
            db.session.query(User_Playlist, Tracks, Creator)
            .filter(User_Playlist.playlist_id == i.playlist_id)
            .join(Tracks, User_Playlist.track_id == Tracks.track_id)
            .join(Creator, Tracks.creator_id == Creator.creator_id)
            .all()
        )
        for j in fav_playlist_track:
            fav_playlist_tracks.append(j)

    liked_album_id = Album_likes_stats.query.filter_by(user_id=current_user.id).all()
    liked_albums = []
    for i in liked_album_id:
        album = get_album(i.album_id)
        liked_albums.append(album)

    liked_track_id = Track_likes_stats.query.filter_by(
        user_id=current_user.id, value=1
    ).all()
    liked_tracks = []
    for i in liked_track_id:
        track = get_single(i.track_id)
        liked_tracks.append(track)

    return render_template(
        "user/favorites.html",
        creator_signup_status=creator,
        artists_followed=artists_followed,
        fav_playlists=fav_playlists,
        fav_playlist_tracks=fav_playlist_tracks,
        liked_albums=liked_albums,
        liked_tracks=liked_tracks,
    )


@user.route("/meloverse/u/<user>/my_playlists", methods=["GET", "POST"])
@login_required
def user_playlists(user):
    if request.method == "POST":
        if request.form.get("createPlaylist") == "yes":
            plalist_name = request.form.get("playlistName")
            tracks = request.form.getlist("selectedTracks")
            user = current_user.id
            new_playlist = Playlist(playlist_name=plalist_name, user=user)
            db.session.add(new_playlist)
            db.session.commit()

            playlist_id = new_playlist.playlist_id
            for i in range(len(tracks)):
                playlist_track = User_Playlist(
                    playlist_id=playlist_id, track_id=int(tracks[i])
                )
                db.session.add(playlist_track)
            db.session.commit()

            flash("Playlist Created 🎊")

        elif request.form.get("deletePlaylist") == "yes":
            playlist_id = request.form.get("playlist_id")
            tracks2Del = User_Playlist.query.filter_by(playlist_id=playlist_id).all()
            for i in tracks2Del:
                db.session.delete(i)
            playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
            db.session.delete(playlist)
            db.session.commit()
            flash("Playlist Deleted")

        elif request.form.get("editPlaylist") == "yes":
            playlist_id = request.form.get("playlistId")
            playlist_tracks = User_Playlist.query.filter_by(
                playlist_id=playlist_id
            ).all()
            for i in playlist_tracks:
                db.session.delete(i)
            db.session.commit()
            selected_tracks = request.form.getlist("selectedTracks")
            for i in selected_tracks:
                update_playlist_track = User_Playlist(
                    playlist_id=playlist_id, track_id=i
                )
                db.session.add(update_playlist_track)
            db.session.commit()
            flash("Playlist edited✌️")

        elif request.form.get("reaction") == "like":
            playlist_id = request.form.get("playlist_id")
            playlist_duplicate = Playlist_likes_stats.query.filter(
                Playlist_likes_stats.user_id == current_user.id,
                Playlist_likes_stats.playlist_id == playlist_id,
            ).first()  # does playlist with same atributes already exist?
            if playlist_duplicate == None:
                new_record = Playlist_likes_stats(
                    user_id=current_user.id, playlist_id=playlist_id
                )
                db.session.add(new_record)
                db.session.commit()
            else:
                db.session.delete(playlist_duplicate)  # remove from fav
                db.session.commit()

        return redirect(url_for("user.user_playlists", user=current_user.username))

    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    tracks = Tracks.query.order_by(Tracks.track_name).all()
    playlists = (
        db.session.query(Playlist, User_Playlist, Playlist_likes_stats)
        .filter(Playlist.user == current_user.id)
        .join(User_Playlist, User_Playlist.playlist_id == Playlist.playlist_id)
        .outerjoin(
            Playlist_likes_stats,
            Playlist.playlist_id == Playlist_likes_stats.playlist_id,
        )
        .all()
    )

    playlist_Ids = []
    playlist_dict = dict()
    for x, y, z in playlists:
        p_id = x.playlist_id
        playlist_Ids.append(p_id)
        t_id = y.track_id
        if p_id not in playlist_dict.keys():
            playlist_dict[p_id] = [t_id]
        else:
            playlist_dict[p_id].append(t_id)

    playlist_tracks = []
    for i in set(playlist_Ids):
        playlist_tracks += (
            db.session.query(User_Playlist, Tracks, Creator.creator_name)
            .filter(User_Playlist.playlist_id == i)
            .join(Tracks, User_Playlist.track_id == Tracks.track_id)
            .join(Creator, Tracks.creator_id == Creator.creator_id)
            .all()
        )

    return render_template(
        "user/user_playlists.html",
        creator_signup_status=creator,
        tracks=tracks,
        playlists=playlists,
        playlist_dict=playlist_dict,
        playlist_tracks=playlist_tracks,
    )


@user.route("/meloverse/u/<user>/discover", methods=["GET", "POST"])
@login_required
def discover(user):
    if request.method == "POST":
        user = current_user.id
        reaction = request.form.get("reaction")
        announcement_id = request.form.get("announcement_id")
        announcement = Announcement.query.filter_by(
            announcement_id=announcement_id
        ).first()
        already_liked = Announcement_stats.query.filter_by(
            announcement_id=announcement_id, user_id=user
        ).first()

        if already_liked:
            if reaction == "like" and already_liked.value != 1:
                already_liked.value = 1
                announcement.likes += 1
                announcement.dislikes -= 1
            elif reaction == "dislike" and already_liked.value != -1:
                already_liked.value = -1
                announcement.dislikes += 1
                announcement.likes -= 1
        else:
            if reaction == "like":
                new_announcement_stat = Announcement_stats(
                    announcement_id=announcement_id, user_id=user, value=1
                )
                announcement.likes += 1
            elif reaction == "dislike":
                new_announcement_stat = Announcement_stats(
                    announcement_id=announcement_id, user_id=user, value=-1
                )
                announcement.dislikes += 1
            db.session.add(new_announcement_stat)

        db.session.commit()
    announcements = (
        db.session.query(Announcement, Creator)
        .join(Announcement, Announcement.creator == Creator.creator_name)
        .order_by(Announcement.date.desc())
        .limit(10)
        .all()
    )

    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    return render_template(
        "user/discover.html", announcements=announcements, creator_signup_status=creator
    )


@user.route("/meloverse/u/<user>/search/", methods=["GET", "POST"])
@login_required
def search(user):
    if request.method == "POST":
        query = request.form.get("search")
        creators, albums, tracks, genre = search_query(query)

    liked_albums = []
    if albums:
        for x, y, z in albums:
            album_id = x.album_id
            user_id = current_user.id
            item = Album_likes_stats.query.filter(
                Album_likes_stats.album_id == album_id,
                Album_likes_stats.user_id == user_id,
            ).first()
            if item != None:
                liked_albums.append(album_id)

    liked_tracks, disliked_tracks = [], []

    if tracks:
        for x, y, z in tracks:
            track_id = x.track_id
            user_id = current_user.id
            item = Track_likes_stats.query.filter(
                Track_likes_stats.track_id == track_id,
                Track_likes_stats.user_id == user_id,
            ).first()
            if item != None and item.value == 1:
                liked_tracks.append(track_id)
            elif item != None and item.value == -1:
                disliked_tracks.append(track_id)

    if genre:
        for x, y, z in genre:
            track_id = x.track_id
            user_id = current_user.id
            item = Track_likes_stats.query.filter(
                Track_likes_stats.track_id == track_id,
                Track_likes_stats.user_id == user_id,
            ).first()
            if item != None and item.value == 1:
                liked_tracks.append(track_id)
            elif item != None and item.value == -1:
                disliked_tracks.append(track_id)

    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    return render_template(
        "user/search.html",
        creators=creators,
        albums=albums,
        tracks=tracks,
        query=query,
        genre=genre,
        creator_signup_status=creator,
        liked_albums=set(liked_albums),
        liked_tracks=set(liked_tracks),
        disliked_tracks=set(disliked_tracks),
    )


@user.route("creator_center/<user>/", methods=["GET", "POST"])
@login_required
def creator_dashboard(user):
    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    if request.method == "POST":
        song_id = request.form.get("song_id")
        song = Tracks.query.filter_by(track_id=song_id).first()
        if song != None and request.form.get("delete_song") == "yes":
            db.session.delete(song)
            creator.songs_published -= 1
            if song.album_id == 0 or song.album_id == "0":
                creator.no_of_singles -= 1
            else:
                album = Album.query.filter_by(album_id=song.album_id).first()
                album.no_of_tracks -= 1
                if album.no_of_tracks == 0:
                    db.session.delete(album)
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

        if song != None and request.form.get("edit_song") == "yes":
            song_name = request.form.get("song_name")
            artists = request.form.get("artists")
            genre = request.form.get("genre")
            lyrics = request.form.get("lyrics")
            duration = request.form.get("duration")

            song = Tracks.query.filter_by(track_id=song_id).first()
            if song_name != "":
                song.track_name = song_name
            if artists != "":
                song.artists = artists
            if genre != "":
                song.genre = genre
            if lyrics != "":
                song.lyrics = lyrics
            if duration != "":
                song.duration = duration
            db.session.commit()

        if album != None and request.form.get("edit_album") == "yes":
            album_name = request.form.get("album_name")
            release_year = request.form.get("release_year")
            genre = request.form.get("genre")
            description = request.form.get("description")

            if album_name != "":
                album.album_name = album_name
            if release_year != "":
                album.release_year = release_year
            if genre != "":
                album.genre = genre
            if description != "":
                album.description = description
            db.session.commit()

    id = current_user.id
    albums = Album.query.filter_by(creator_id=id).all()
    singles = Tracks.query.filter_by(creator_id=id, album_id=0).all()
    songs = (
        db.session.query(Tracks, Album.album_name)
        .join(Album, Tracks.album_id == Album.album_id)
        .filter(Tracks.creator_id == id)
        .all()
    )

    singles_published = creator.no_of_singles
    albums_published = creator.no_of_albums
    status = any([singles_published, albums_published])

    most_liked_song = (
        Tracks.query.filter_by(creator_id=id).order_by(Tracks.likes.desc()).first()
    )

    most_liked_album = (
        db.session.query(Album.album_name, func.max(Tracks.likes).label("likes"))
        .join(Tracks, Album.album_id == Tracks.album_id)
        .join(Creator, Album.creator_id == id)
        .filter(Creator.creator_id == id)
        .group_by(Album.album_id)
        .order_by(func.max(Tracks.likes).desc())
        .first()
    )

    most_played_song = (
        Tracks.query.filter_by(creator_id=current_user.id)
        .order_by(Tracks.plays.desc())
        .first()
    )

    most_played_album = (
        db.session.query(Album.album_name, func.max(Tracks.plays).label("plays"))
        .join(Tracks, Album.album_id == Tracks.album_id)
        .join(Creator, Album.creator_id == id)
        .filter(Creator.creator_id == id)
        .group_by(Album.album_id)
        .order_by(func.max(Tracks.plays).desc())
        .first()
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
        .filter(Creator.creator_id == id)
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
        "creator/creator_center.html",
        status=status,
        creator=creator,
        singles=singles,
        songs=songs,
        albums=albums,
        most_liked_song=most_liked_song,
        most_liked_album=most_liked_album,
        most_played_song=most_played_song,
        most_played_album=most_played_album,
        songs_published=singles_published,
        albums_published=albums_published,
        album_obj=album_obj,
    )


@user.route("creator_center/<user>/new", methods=["GET", "POST"])
@login_required
def new(user):
    return render_template("creator/new.html")


@user.route("creator_center/<user>/profile", methods=["GET", "POST"])
@login_required
def profile(user):
    if request.form.get("edit_profile") == "True":
        return redirect(url_for("user.edit_profile", user=current_user.username))
    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    return render_template("creator/profile.html", bio=creator.bio)


@user.route("creator_center/<user>/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile(user):
    creator = Creator.query.filter_by(creator_id=current_user.id).first()
    if request.method == "POST":
        name = request.form["name"]
        bio = request.form["bio"]
        user = Users.query.filter_by(id=current_user.id).first()
        if user and creator:
            if name != "":
                user.username = name
            if bio != "":
                creator.bio = bio
            db.session.commit()
        return redirect(url_for("user.profile", user=current_user.username))
    return render_template("creator/edit_profile.html", creator=creator)


@user.route("creator_center/<user>/announcement", methods=["GET", "POST"])
@login_required
def announcement(user):
    if request.method == "POST":
        announcement = request.form.get("announcement")
        if announcement != "":
            creator = current_user.username
            heading = request.form.get("heading")
            link = request.form.get("link")
            date = datetime.now()
            new_annoucement = Announcement(
                announcement=announcement,
                date=date,
                creator=creator,
                heading=heading,
                link=link,
            )
            db.session.add(new_annoucement)
            db.session.commit()
            flash("Annoucement Posted 🎊")
    return render_template("creator/announcement.html", user=current_user.username)


@user.route("creator_center/<user>/new_single", methods=["GET", "POST"])
@login_required
def new_single(user):
    if request.method == "POST":
        song_name = request.form.get("song_name")
        artists = request.form.get("artists")
        genre = request.form.get("genre")
        lyrics = request.form.get("lyrics")
        duration = request.form.get("duration")
        creator_id = current_user.id
        date = datetime.now().date()
        file = request.files["song_file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        new_song = Tracks(
            track_name=song_name,
            artists=artists,
            creator_id=creator_id,
            date_created=date,
            track_file=filename,
            genre=genre,
            lyrics=lyrics,
            duration=duration,
        )
        db.session.add(new_song)
        no_of_singles_update = text(
            "update creator set no_of_singles=no_of_singles+1 where creator_id= :id"
        )
        db.session.execute(no_of_singles_update, {"id": creator_id})
        no_of_songs_update = text(
            "update creator set songs_published=songs_published+1 where creator_id= :id"
        )
        db.session.execute(no_of_songs_update, {"id": creator_id})
        db.session.commit()
        return render_template(
            "creator/success.html", user=current_user.username, song_or_album="song"
        )
    return render_template("creator/new_single.html", user=current_user)


@user.route("creator_center/<user>/<album>/add_track", methods=["GET", "POST"])
@login_required
def add_track(user, album):
    album = Album.query.filter_by(creator_id=current_user.id, album_name=album).first()
    if request.method == "POST":
        song_name = request.form.get("song_name")
        artists = request.form.get("artists")
        genre = album.genre
        lyrics = request.form.get("lyrics")
        duration = request.form.get("duration")
        creator_id = album.creator_id
        date = datetime.now().date()
        file = request.files["song_file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        new_track = Tracks(
            track_name=song_name,
            artists=artists,
            creator_id=creator_id,
            date_created=date,
            track_file=filename,
            genre=genre,
            lyrics=lyrics,
            duration=duration,
            album_id=album.album_id,
        )
        db.session.add(new_track)
        no_of_album_tracks_update = text(
            "update album set no_of_tracks=no_of_tracks+1 where creator_id= :id and album_id= :album_id"
        )
        db.session.execute(
            no_of_album_tracks_update, {"id": creator_id, "album_id": album.album_id}
        )
        no_of_songs_update = text(
            "update creator set songs_published=songs_published+1 where creator_id= :id"
        )
        db.session.execute(no_of_songs_update, {"id": creator_id})
        db.session.commit()
        add_track = request.form.get("add_track")
        publish = request.form.get("publish")
        if add_track == "True":
            return render_template(
                "creator/add_track.html", user=current_user.username, album=album
            )
        elif publish == "True":
            return render_template(
                "creator/success.html",
                user=current_user.username,
                song_or_album="album",
            )
    return render_template(
        "creator/add_track.html", user=current_user.username, album=album
    )


@user.route("creator_center/<user>/new_album", methods=["GET", "POST"])
@login_required
def new_album(user):
    if request.method == "POST":
        album_name = request.form.get("album_name")
        year = datetime.now().year
        genre = request.form.get("genre")
        description = request.form.get("album_description")
        date_created = datetime.now().date()
        creator_id = current_user.id
        new_album = Album(
            album_name=album_name,
            release_year=year,
            genre=genre,
            description=description,
            creator_id=creator_id,
            date_created=date_created,
        )
        db.session.add(new_album)
        no_of_albums_update = text(
            "update creator set no_of_albums=no_of_albums+1 where creator_id= :id"
        )
        db.session.execute(no_of_albums_update, {"id": creator_id})
        db.session.commit()
        add_track = request.form.get("add_track")
        if add_track == "True":
            return redirect(
                url_for("user.add_track", user=current_user.username, album=album_name)
            )
    return render_template("creator/new_album.html", user=current_user.username)


@user.route("user/<user>/creator/<creator>", methods=["GET", "POST"])
@login_required
def creator_profile(user, creator):
    creator = Creator.query.filter_by(creator_id=creator).first()
    if request.method == "POST":
        reaction = request.form.get("reaction")
        if reaction == "follow":
            new_fan = whois_Followeing_who(
                fan_id=current_user.id, fan_of=creator.creator_id
            )
            db.session.add(new_fan)
            creator.followers += 1
            db.session.commit()

        elif reaction == "unfollow":
            ex_Fan = whois_Followeing_who.query.filter_by(
                fan_id=current_user.id, fan_of=creator.creator_id
            ).first()
            db.session.delete(ex_Fan)
            creator.followers -= 1
            db.session.commit()

    follow_status = whois_Followeing_who.query.filter_by(
        fan_id=current_user.id, fan_of=creator.creator_id
    ).first()

    singles = Tracks.query.filter_by(creator_id=creator.creator_id, album_id=0).all()

    songs = (
        db.session.query(Tracks, Album.album_name)
        .join(Album, Tracks.album_id == Album.album_id)
        .filter(Tracks.creator_id == creator.creator_id)
        .all()
    )

    tracks_alias = aliased(Tracks)
    creator_or_not = Creator.query.filter_by(creator_id=current_user.id).first()
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
    album_tracks = (
        db.session.query(Album, Tracks)
        .filter(Album.creator_id == creator.creator_id)
        .join(Album, Album.album_id == Tracks.album_id)
        .all()
    )

    return render_template(
        "user/creator_profile.html",
        creator=creator,
        singles=singles,
        songs=songs,
        albums_obj=album_obj,
        follow_status=follow_status,
        creator_signup_status=creator_or_not,
        album_tracks=album_tracks,
    )


@user.route("/update_timeline", methods=["POST"])
@login_required
def update_timeline():
    if (
        request.method == "POST"
        and request.headers.get("Content-Type") == "application/json"
    ):
        try:
            data = request.get_json()
            user_id = data.get("userId")
            track_id = data.get("trackId")
            track = Tracks.query.filter_by(track_id=track_id).first()
            event_time = datetime.now().date()
            track.plays += 1
            new_event = usage_timeline(
                user_id=user_id,
                track_id=track_id,
                album_id=track.album_id,
                date_time=event_time,
            )
            db.session.add(new_event)
            db.session.commit()
        except Exception as e:
            pass
        return jsonify({"message": "Usage timeline updated"}), 200


@user.route("/update_like_dislike", methods=["POST"])
@login_required
def update_like_dislike():
    if (
        request.method == "POST"
        and request.headers.get("Content-Type") == "application/json"
    ):
        try:
            data = request.get_json()
            user_id = data.get("userId")
            track_id = data.get("trackId")
            like_status = data.get("likeStatus")
            # Add your logic for handling like/dislike here
            print(
                f"Received like/dislike request for user {user_id}, track {track_id}, status: {like_status}"
            )
            return jsonify({"message": "Like/Dislike updated successfully"}), 200
        except Exception as e:
            print(f"Error processing like/dislike request: {str(e)}")
            return jsonify({"error": "Failed to update like/dislike status"}), 500
    else:
        return jsonify({"error": "Invalid request"}), 400


@user.route("/album_like", methods=["POST"])
@login_required
def album_like():
    try:
        data = request.get_json()
        album_id = data.get("album_id")
        user_id = current_user.id
        already_liked = Album_likes_stats.query.filter_by(
            album_id=album_id, user_id=user_id
        ).first()
        if already_liked == None:
            new_record = Album_likes_stats(user_id=user_id, album_id=album_id)
            db.session.add(new_record)
            db.session.commit()
        else:
            db.session.delete(already_liked)
            db.session.commit()
        return jsonify({"success": True, "message": "Album liked"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@user.route("/track_like", methods=["POST"])
@login_required
def track_like():
    try:
        data = request.get_json()
        track_id = data.get("track_id")
        user_id = current_user.id
        like_value = int(data.get("like_value"))
        already_liked = Track_likes_stats.query.filter_by(
            track_id=track_id, user_id=user_id
        ).first()
        track = Tracks.query.filter_by(track_id=track_id).first()
        if already_liked == None:
            new_record = Track_likes_stats(
                user_id=user_id, track_id=track_id, value=like_value
            )
            if like_value == 1:
                track.likes += 1
            else:
                track.dislikes += 1
            db.session.add(new_record)
            db.session.commit()
        else:
            if like_value == 1 and already_liked.value == -1:
                already_liked.value = 1
                track.likes += 1
                track.dislikes -= 1
            elif like_value == -1 and already_liked.value == 1:
                already_liked.value = -1
                track.dislikes += 1
                track.likes -= 1
            else:
                db.session.delete(already_liked)
                if already_liked.value == 1:
                    track.likes -= 1
                else:
                    track.dislikes -= 1
            db.session.commit()

        return jsonify({"success": True, "message": "Album liked"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
