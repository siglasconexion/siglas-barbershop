import os
from flask import Flask
from src.extensions import db

# from .routes.person_routes import person
from src.extensions import db


def create_app():
    app = Flask(__name__)

    # app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    # app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # db.init_app(app)  # esta y las 2 de arribas activarlas luego

    from src import models

    # from src.routes import person

    # app.register_blueprint(person, url_prefix="/person")

    from src.routes import register_blueprints

    register_blueprints(app)

    @app.route("/")
    def home():
        return "Hello World"

    return app
