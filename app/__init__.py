from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime, timezone
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)


    @app.template_filter('to_utc')
    def to_utc(value):
        """Convert a datetime to UTC."""
        if value and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    
    # Load config
    app.config.from_mapping(
        SECRET_KEY='dev',  # Change in production!
        SQLALCHEMY_DATABASE_URI='sqlite:///puzzle_site.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    login_manager.init_app(app)


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .models import User, Issue, Puzzle, Submission
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'Issue': Issue,
            'Puzzle': Puzzle,
            'Submission': Submission
        }
    # Import and register blueprints
    from . import routes
    app.register_blueprint(routes.bp)
    app.register_blueprint(routes.admin_bp)

    from .auth import auth
    app.register_blueprint(auth)

    from . import models

    from .puzzles import puzzle_bp
    app.register_blueprint(puzzle_bp)

    return app

