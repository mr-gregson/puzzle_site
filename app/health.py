"""
Health check endpoints for monitoring and deployment.
"""
from flask import Blueprint, jsonify, current_app
from app import db
from app.models import User
import os
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@health_bp.route('/health/detailed')
def detailed_health_check():
    """Detailed health check including database connectivity."""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'checks': {}
    }
    
    # Database connectivity check
    try:
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
    
    # Environment check
    required_env_vars = ['SECRET_KEY', 'DATABASE_URL']
    env_missing = []
    
    for var in required_env_vars:
        if not os.environ.get(var):
            env_missing.append(var)
    
    if env_missing:
        health_status['status'] = 'unhealthy'
        health_status['checks']['environment'] = {
            'status': 'unhealthy',
            'message': f'Missing environment variables: {", ".join(env_missing)}'
        }
    else:
        health_status['checks']['environment'] = {
            'status': 'healthy',
            'message': 'All required environment variables present'
        }
    
    # Disk space check (basic)
    try:
        import shutil
        total, used, free = shutil.disk_usage('/')
        free_percent = (free / total) * 100
        
        if free_percent < 10:
            health_status['status'] = 'unhealthy'
            health_status['checks']['disk_space'] = {
                'status': 'unhealthy',
                'message': f'Low disk space: {free_percent:.1f}% free'
            }
        else:
            health_status['checks']['disk_space'] = {
                'status': 'healthy',
                'message': f'Disk space OK: {free_percent:.1f}% free'
            }
    except Exception as e:
        health_status['checks']['disk_space'] = {
            'status': 'unknown',
            'message': f'Could not check disk space: {str(e)}'
        }
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@health_bp.route('/readiness')
def readiness_check():
    """Kubernetes readiness probe endpoint."""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        current_app.logger.error(f'Readiness check failed: {e}')
        return jsonify({'status': 'not ready', 'error': str(e)}), 503

@health_bp.route('/liveness')
def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return jsonify({'status': 'alive'}), 200