from .database import db
from flask_login import UserMixin


class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False, default="user")



class Creator(db.Model):
    __tablename__ = 'creator'
    creator_id=db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    creator_name=db.Column(db.String, db.ForeignKey("users.username"))
    creator_email=db.Column(db.String, db.ForeignKey("users.email"))
    bio=db.Column(db.String)


class Tracks(db.Model):
    __tablename__ = 'tracks'
    track_id=db.Column(db.Integer, autoincrement=True, primary_key=True)
    track_name=db.Column(db.String, nullable=False)
    artists=db.Column(db.String, nullable=False)
    creator_id=db.Column(db.String, db.ForeignKey("creator.creator_name"))
    track_link=db.Column(db.String, nullable=False)
    genre=db.Column(db.String)
    lyrics=db.Column(db.String)
    duration=db.Column(db.String)
    date_created=db.Column(db.Date)
    album_id=db.Column(db.String, default='Null')


class Album(db.Model):
    __tablename__='album'
    album_id=db.Column(db.Integer, autoincrement=True, primary_key=True)
    album_name=db.Column(db.String, nullable=False)
    release_year=db.Column(db.String)
    genre=db.Column(db.String)
    description=db.Column(db.String)


class Playlist(db.Model):
    __tablename__='playlist'
    playlist_id=db.Column(db.Integer, autoincrement=True, primary_key=True)
    playlist_name=db.Column(db.String)
    user=db.Column(db.Integer, db.ForeignKey("user.id"))


class User_Playlist(db.Model):
    __tablename__='user_playlist'
    playlist_id=db.Column(db.Integer, db.ForeignKey("playlist.playlist_id"), primary_key=True)
    track_id=db.Column(db.Integer, db.ForeignKey("tracks.track_id"), primary_key=True)


class Announcement(db.Model):
    __tablename__='announcement'
    announcement_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    heading=db.Column(db.String, nullable=False)
    announcement=db.Column(db.String, nullable=False)
    creator=db.Column(db.String, db.ForeignKey("creator.creator_name"))
    link=db.Column(db.String, default="Null")
    date=db.Column(db.Date)
    likes=db.Column(db.Integer, default=0)
    dislikes=db.Column(db.Integer, default=0)


class Announcement_stats(db.Model):
    __tablename__='announcement_stats'
    announcement_id=db.Column(db.Integer, db.ForeignKey("announcement.announcement_id"), primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    #1 for like, -1 for dislike, default 0
    value=db.Column(db.Integer, default=0)