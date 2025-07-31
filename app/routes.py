from flask import Blueprint, request, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from flask_login import login_required
from datetime import datetime, timezone
from .models import User, Puzzle, Hint, Issue
from .forms import PuzzleForm, HintForm, IssueForm
from . import db
from .admin_utils import admin_required
from app.puzzles import normalize_answer

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash("Cannot delete another admin.")
        return redirect(url_for('admin.user_list'))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted.")
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/add_issue', methods=['GET', 'POST'])
@login_required
@admin_required
def add_issue():
    form = IssueForm()
    
    if form.validate_on_submit():
        new_issue = Issue(
            title=form.title.data,
            description=form.description.data,
            pdf_filename=form.pdf_filename.data or None,
            available_date=form.available_date.data
        )
        db.session.add(new_issue)
        db.session.commit()
        flash('Issue created successfully!')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin_add_puzzle.html', form=form)

@admin_bp.route('/add_puzzle', methods=['GET', 'POST'])
@login_required
@admin_required
def add_puzzle():
    form = PuzzleForm()
    form.issue_id.choices = [(0, '-- No Issue --')] + [
        (i.id, i.title) for i in Issue.query.order_by(Issue.id).all()
    ]

    if form.validate_on_submit():
        issue_id = form.issue_id.data if form.issue_id.data != 0 else None
        new_puzzle = Puzzle(
            title=form.title.data,
            description=form.description.data,
            answer_hash=generate_password_hash(normalize_answer(form.answer.data)),
            issue_id=issue_id
        )
        db.session.add(new_puzzle)
        db.session.commit()
        flash('Puzzle created successfully!')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin_add_puzzle.html', form=form)

@admin_bp.route('/add_hint', methods=['GET', 'POST'])
@login_required
@admin_required
def add_hint():
    form = HintForm()
    form.puzzle_id.choices = [(p.id, p.title) for p in Puzzle.query.order_by(Puzzle.id).all()]

    if form.validate_on_submit():
        new_hint = Hint(
            puzzle_id=form.puzzle_id.data,
            hint_text=form.hint_text.data,
            unlock_date=form.unlock_date.data
        )
        db.session.add(new_hint)
        db.session.commit()
        flash('Hint added successfully!')
        return redirect(url_for('admin.user_list'))
    
    return render_template('admin_add_hint.html', form=form)

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    return render_template('admin_dashboard.html')



bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('puzzle.list_puzzles'))