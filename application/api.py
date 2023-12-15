from flask_restful import Resource, reqparse, fields, marshal_with
from application.validation import BusinessValidationError, NotFoundError
from application.models import Users, Tracks, Creator
from flask import request, abort, jsonify


class SongAPI(Resource):
    def get(self):
        user_id = request.args.get("user_id")
        song_id = request.args.get("song_id")

        user = Users.query.get(user_id)
        song = Tracks.query.get(song_id)
        creator = Creator.query.get(song.creator_id)

        if not user or not song or not creator:
            return jsonify({"message": "User, song, or creator not found"}), 404

        user_data = {
            column.name: getattr(user, column.name)
            for column in Users.__table__.columns
        }
        song_data = {
            column.name: getattr(song, column.name)
            for column in Tracks.__table__.columns
        }
        creator_data = {
            column.name: getattr(creator, column.name)
            for column in Creator.__table__.columns
        }

        return jsonify({"song": song_data, "user": user_data, "creator": creator_data})
