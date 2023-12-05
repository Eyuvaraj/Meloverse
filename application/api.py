from flask_restful import Resource, reqparse, fields, marshal_with
from application.validation import BusinessValidationError, NotFoundError
from application.models import Users, Tracks, Creator
from flask import request, abort, jsonify

# get_song = reqparse.RequestParser()
# get_song.add_argument("user_id", type=int, required=True, help="User ID is required")
# get_song.add_argument("song_id", type=int, required=True, help="Song ID is required")

# resource_fields = {
#     "song_id": fields.Integer,
#     "song_name": fields.String,
#     "user_id": fields.Integer,
#     "creator": fields.Nested(
#         {
#             "creator_id": fields.Integer,
#             "creator_name": fields.String,
#             # Add other fields you want to include from the Creator model
#         }
#     ),
# }


class SongAPI(Resource):
    def get(self):
        user_id = request.args.get("user_id")
        song_id = request.args.get("song_id")

        user = Users.query.get(user_id)
        song = Tracks.query.get(song_id)
        creator = Creator.query.get(song.creator_id)

        # Check if user, song, and creator exist
        if not user or not song or not creator:
            return jsonify({"message": "User, song, or creator not found"}), 404

        # Create a nested structure with column names and values
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

        # Return the nested structure
        return jsonify({"song": song_data, "user": user_data, "creator": creator_data})


"""
    def put(self, username):
        args = update_user_parser.parse_args()
        return {'hello': 'world'}        

    @marshal_with(resource_fields)
    def post(self):
        args = create_user_parser.parse_args()
        username = args.get("username", None)
        email = args.get("email", None)

        if username is None:
            raise BusinessValidationError(status_code=400, error_code="BE1001", error_message="username is required")

        if email is None:
            raise BusinessValidationError(status_code=400, error_code="BE1002", error_message="email is required")

        if "@" in email:
            pass
        else:
            raise BusinessValidationError(status_code=400, error_code="BE1003", error_message="Invalid email")

        user = db.session.query(User).filter((User.username == username) | (User.email == email)).first()
        if user:
            raise BusinessValidationError(status_code=400, error_code="BE1004", error_message="Duplicate user")            

        new_user = User(username=username, email=email)
        db.session.add(new_user)
        db.session.commit()
        return new_user                

    def delete(self, username):
        return {'hello': 'world'}
"""
