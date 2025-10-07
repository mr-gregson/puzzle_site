from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail, db

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail as SGMail
except Exception:
    SendGridAPIClient = None
    SGMail = None

def send_async_email(app, msg):
    """Send email asynchronously in background thread"""
    with app.app_context():
        mail.send(msg)


def send_async_sendgrid(app, subject, to, html):
    """Send email asynchronously via SendGrid Web API"""
    with app.app_context():
        api_key = app.config.get('SENDGRID_API_KEY')
        if not api_key or SendGridAPIClient is None:
            current_app.logger.error('SendGrid API not available or API key missing')
            return
        client = SendGridAPIClient(api_key)
        from_email = app.config['MAIL_DEFAULT_SENDER']
        to_list = to if isinstance(to, list) else [to]
        sg_msg = SGMail(
            from_email=from_email,
            to_emails=to_list,
            subject=f'[Puzzle Site] {subject}',
            html_content=html,
        )
        client.send(sg_msg)

def send_email(to, subject, template, **kwargs):
    """Send email using selected provider"""
    app = current_app._get_current_object()
    html = render_template(template, **kwargs)
    provider = app.config.get('MAIL_PROVIDER', 'smtp').lower()

    if provider == 'sendgrid':
        thr = Thread(target=send_async_sendgrid, args=[app, subject, to, html])
        thr.start()
        return thr
    else:
        msg = Message(
            subject=f'[Puzzle Site] {subject}',
            recipients=[to] if isinstance(to, str) else to,
            html=html,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()
        return thr

def send_welcome_email(user):
    """Send welcome email to new users"""
    return send_email(
        user.email,
        'Welcome to Puzzle Site!',
        'email/welcome.html',
        user=user
    )


def send_new_issue_notification(user, issue):
    """Send notification about new issue"""
    return send_email(
        user.email,
        f'New Issue Available: {issue.title}',
        'email/new_issue.html',
        user=user,
        issue=issue
    )


def send_new_hint_notification(user, puzzle, hint):
    """Send notification about new hint"""
    return send_email(
        user.email,
        f'New Hint for: {puzzle.title}',
        'email/new_hint.html',
        user=user,
        puzzle=puzzle,
        hint=hint
    )


def send_password_reset_email(user, token):
    """Send password reset email"""
    return send_email(
        user.email,
        'Password Reset Request',
        'email/password_reset.html',
        user=user,
        token=token
    )


def notify_all_users_new_issue(issue):
    """Send new issue notification to all users with notifications enabled"""
    from .models import User
    
    # Get all users who want issue notifications
    users = User.query.filter_by(
        email_notifications=True,
        notify_new_issues=True
    ).all()
    
    threads = []
    for user in users:
        thread = send_new_issue_notification(user, issue)
        threads.append(thread)
    
    return threads


def notify_users_new_hint(puzzle, hint):
    """Send new hint notification to users who have attempted this puzzle"""
    from .models import User, Submission
    
    # Get users who have submitted to this puzzle and want hint notifications
    user_ids = db.session.query(Submission.user_id).filter_by(puzzle_id=puzzle.id).distinct()
    users = User.query.filter(
        User.id.in_(user_ids),
        User.email_notifications == True,
        User.notify_new_hints == True
    ).all()
    
    threads = []
    for user in users:
        thread = send_new_hint_notification(user, puzzle, hint)
        threads.append(thread)
    
    return threads