from . import db
from datetime import datetime, timezone
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    display_name = db.Column(db.String(150), nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Email notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    notify_new_issues = db.Column(db.Boolean, default=True)
    notify_new_hints = db.Column(db.Boolean, default=True)

    submissions = db.relationship('Submission', backref='user', lazy=True)
    
    def generate_password_reset_token(self):
        """Generate a secure token for password reset"""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})
    
    @staticmethod
    def verify_password_reset_token(token, expires_sec=3600):
        """Verify password reset token and return user if valid"""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expires_sec)
            user_id = data['user_id']
        except:
            return None
        return User.query.get(user_id)

class Puzzle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    answer_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=True)

    hints = db.relationship('Hint', backref='puzzle', lazy=True)
    submissions = db.relationship('Submission', backref='puzzle', lazy=True)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    puzzle_id = db.Column(db.Integer, db.ForeignKey('puzzle.id'), nullable=False)
    submitted_answer = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Hint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    puzzle_id = db.Column(db.Integer, db.ForeignKey('puzzle.id'), nullable=False)
    hint_text = db.Column(db.Text, nullable=False)
    unlock_date = db.Column(db.Date, nullable=False)

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    pdf_filename = db.Column(db.String(200), nullable=True)
    available_date = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    puzzles = db.relationship('Puzzle', backref='issue', lazy=True)

