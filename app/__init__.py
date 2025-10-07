from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from datetime import datetime, timezone
import os
import logging
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

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
        SECRET_KEY=os.environ.get('SECRET_KEY') or 'dev-fallback-change-in-production',
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or 'sqlite:///puzzle_site.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Security settings
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_TIME_LIMIT=None,
        SESSION_COOKIE_SECURE=False,
        REMEMBER_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        # Email configuration
        MAIL_SERVER=os.environ.get('MAIL_SERVER') or 'smtp.gmail.com',
        MAIL_PORT=int(os.environ.get('MAIL_PORT') or 587),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1'],
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER'),
        PUZZLE_SITE_ADMIN=os.environ.get('PUZZLE_SITE_ADMIN') or 'admin@example.com',
        MAIL_PROVIDER=os.environ.get('MAIL_PROVIDER', 'smtp'),  # 'smtp' or 'sendgrid'
        SENDGRID_API_KEY=os.environ.get('SENDGRID_API_KEY'),
        # Logging
        LOG_LEVEL=os.environ.get('LOG_LEVEL', 'INFO'),
    )

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)


    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
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
    
    # Register health check endpoints
    from .health import health_bp
    app.register_blueprint(health_bp)
    
    # Register error handlers
    from .errors import register_error_handlers
    register_error_handlers(app)

    # Initialize email scheduler
    from .scheduler import scheduler
    scheduler.init_app(app)
    
    # Start scheduler in development (not recommended for production)
    if app.config.get('ENV') != 'production':
        scheduler.start()
    
    # Configure logging for production
    configure_logging(app)
    
    # Add security headers
    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        if app.config.get('ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    return app

def configure_logging(app):
    """Configure logging for the application."""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/puzzle_site.log', 
                                         maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
        app.logger.info('Puzzle site startup')

