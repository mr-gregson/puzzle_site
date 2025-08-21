from datetime import datetime, timezone, timedelta
from flask import current_app
from .models import Issue, Hint, User, Submission
from .email import notify_all_users_new_issue, notify_users_new_hint
from . import db
import threading
import time


class EmailScheduler:
    """Background scheduler for sending email notifications"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.app = None
    
    def init_app(self, app):
        """Initialize the scheduler with Flask app"""
        self.app = app
    
    def start(self):
        """Start the background scheduler thread"""
        if not self.running and self.app:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop the background scheduler thread"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _run_scheduler(self):
        """Main scheduler loop - runs in background thread"""
        with self.app.app_context():
            while self.running:
                try:
                    self._check_new_issues()
                    self._check_new_hints()
                except Exception as e:
                    print(f"Scheduler error: {e}")
                
                # Check every 10 minutes
                time.sleep(600)
    
    def _check_new_issues(self):
        """Check for issues that just became available"""
        now = datetime.now(timezone.utc)
        # Look for issues that became available in the last 10 minutes
        cutoff_time = now - timedelta(minutes=10)
        
        new_issues = Issue.query.filter(
            Issue.available_date <= now,
            Issue.available_date >= cutoff_time
        ).all()
        
        for issue in new_issues:
            try:
                notify_all_users_new_issue(issue)
                print(f"Sent notifications for issue: {issue.title}")
            except Exception as e:
                print(f"Failed to send notifications for issue {issue.title}: {e}")
    
    def _check_new_hints(self):
        """Check for hints that just became available"""
        now = datetime.now(timezone.utc)
        # Look for hints that became available in the last 10 minutes
        cutoff_time = now - timedelta(minutes=10)
        
        new_hints = Hint.query.filter(
            Hint.unlock_date <= now.date(),
            Hint.unlock_date >= cutoff_time.date()
        ).all()
        
        for hint in new_hints:
            try:
                notify_users_new_hint(hint.puzzle, hint)
                print(f"Sent notifications for hint on puzzle: {hint.puzzle.title}")
            except Exception as e:
                print(f"Failed to send notifications for hint on puzzle {hint.puzzle.title}: {e}")


# Global scheduler instance
scheduler = EmailScheduler()