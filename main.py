from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_restful import Resource, Api
import os
from application import config
from application.config import LocalDevelopmentConfig
from application.database import db
from flask import Blueprint
from flask_migrate import Migrate

app = None
api = None

def create_app():
    app = Flask(__name__, template_folder="templates", static_url_path='/static')
    if os.getenv('ENV', "development") == "production":
        raise Exception("Currently no production config is setup.")
    else:
        print("Staring Local Development")
        app.config.from_object(LocalDevelopmentConfig)

    db.init_app(app)
    api = Api(app)
    app.app_context().push()
    migrate= Migrate(app, db)
    return app, api

app, api = create_app()

# Import all the controllers so they are loaded
from application.controllers import *

if __name__ == "__main__":
    app.run(debug=True)