from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Load config
    app.config.from_mapping(
        SECRET_KEY='dev',  # Change in production!
        SQLALCHEMY_DATABASE_URI='sqlite:///puzzle_site.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


    # Import and register blueprints
    from . import routes
    app.register_blueprint(routes.bp)

    from .auth import auth
    app.register_blueprint(auth)

    from . import models

    return app