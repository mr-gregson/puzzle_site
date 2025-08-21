from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db
from .forms import RegisterForm, LoginForm, RequestPasswordResetForm, ResetPasswordForm, UserPreferencesForm
from .email import send_welcome_email, send_password_reset_email

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check for existing username
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.')
            return redirect(url_for('auth.register'))

        # ✅ Check for existing email
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            display_name=form.display_name.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Send welcome email
        try:
            send_welcome_email(new_user)
        except Exception as e:
            # Log the error but don't prevent registration
            print(f"Failed to send welcome email: {e}")
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_password_reset_token()
            try:
                send_password_reset_email(user, token)
                flash('A password reset link has been sent to your email.')
            except Exception as e:
                flash('Failed to send reset email. Please try again later.')
                print(f"Failed to send password reset email: {e}")
        else:
            # Don't reveal that the email doesn't exist for security
            flash('A password reset link has been sent to your email.')
        return redirect(url_for('auth.login'))
    return render_template('request_password_reset.html', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_password_reset_token(token)
    if not user:
        flash('Invalid or expired password reset link.')
        return redirect(url_for('auth.request_password_reset'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Your password has been reset successfully.')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', form=form)

@auth.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    form = UserPreferencesForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.display_name = form.display_name.data
        current_user.email_notifications = form.email_notifications.data
        current_user.notify_new_issues = form.notify_new_issues.data
        current_user.notify_new_hints = form.notify_new_hints.data
        
        db.session.commit()
        flash('Your preferences have been updated successfully.')
        return redirect(url_for('auth.preferences'))
    
    return render_template('user_preferences.html', form=form)
