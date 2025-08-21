"""
WSGI entry point for production deployment.
"""
import os
from app import create_app

# Get the configuration environment
config_name = os.environ.get('FLASK_ENV', 'production')

# Create the Flask application
app = create_app()

# Validate production configuration
if config_name == 'production':
    required_vars = ['SECRET_KEY', 'DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

if __name__ == "__main__":
    app.run()