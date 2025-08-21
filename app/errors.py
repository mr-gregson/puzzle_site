"""
Error handlers for the application.
"""
from flask import render_template, current_app
from app import db

def register_error_handlers(app):
    """Register error handlers with the Flask app."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        current_app.logger.warning(f'404 error: {error}')
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        current_app.logger.error(f'500 error: {error}')
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        current_app.logger.warning(f'403 error: {error}')
        return render_template('errors/404.html'), 403  # Don't reveal 403s exist
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        current_app.logger.warning(f'CSRF error: {e.description}')
        return render_template('errors/500.html'), 400

# Import CSRFError for the error handler
try:
    from flask_wtf.csrf import CSRFError
except ImportError:
    # Create a dummy CSRFError if Flask-WTF is not available
    class CSRFError(Exception):
        pass