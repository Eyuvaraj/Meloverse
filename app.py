from flask import Flask
from flask_restful import Api
import os
from application import config
from application.config import LocalDevelopmentConfig
from application.database import db
from flask import Blueprint
from flask_migrate import Migrate
from application.api import *

app = None
api = None


def create_app():
    app = Flask(__name__, template_folder="templates", static_url_path="/static")
    if os.getenv("ENV", "development") == "production":
        raise Exception("Currently no production config is setup.")
    else:
        print("Staring Local Development")
        app.config.from_object(LocalDevelopmentConfig)

    app.config["SECRET_KEY"] = "23508VWER-515J1PJ155"
    UPLOAD_FOLDER = "static/uploads"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.app_context().push()
    db.init_app(app)
    api = Api(app)

    from application.app_controllers.auth import auth
    from application.app_controllers.users import user
    from application.app_controllers.admin import admin

    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(user, url_prefix="/")
    app.register_blueprint(admin, url_prefix="/")

    return app, api


app, api = create_app()
api.add_resource(SongAPI, "/song")

from application.index import *

if __name__ == "__main__":
    app.run(debug=True)
