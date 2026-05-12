"""
Database migration script for production deployment.
Run this script to set up the production database.
"""
import os
import sys
from flask import Flask
from sqlalchemy import inspect, text
from app import create_app, db
from app.models import User, Issue, Puzzle, Submission, Hint, PuzzleAnswerRule


def _ensure_column_exists(table_name, column_name, ddl_fragment):
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    if column_name in columns:
        return
    db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl_fragment}"))
    db.session.commit()
    print(f"✓ Added column: {table_name}.{column_name}")

def create_database():
    """Create all database tables."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully")

        # Ensure schema updates for existing databases
        _ensure_column_exists('puzzle', 'correct_response', 'TEXT')
        _ensure_column_exists('puzzle', 'incorrect_response', 'TEXT')

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if 'puzzle_answer_rule' not in tables:
            PuzzleAnswerRule.__table__.create(db.engine)
            print('✓ Created table: puzzle_answer_rule')
        
        # Create default admin user if it doesn't exist
        admin_email = os.environ.get('PUZZLE_SITE_ADMIN', 'admin@example.com')
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if not admin_user:
            from werkzeug.security import generate_password_hash
            admin_user = User(
                username='admin',
                email=admin_email,
                password_hash=generate_password_hash('change-this-password'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"✓ Default admin user created: {admin_email}")
            print("⚠️  IMPORTANT: Change the default admin password!")
        else:
            print(f"✓ Admin user already exists: {admin_email}")

def backup_database():
    """Create a backup of the existing database."""
    if os.path.exists('instance/puzzle_site.db'):
        import shutil
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'instance/puzzle_site_backup_{timestamp}.db'
        shutil.copy2('instance/puzzle_site.db', backup_name)
        print(f"✓ Database backed up to: {backup_name}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--backup':
        backup_database()
    
    create_database()
    print("✓ Database setup complete!")