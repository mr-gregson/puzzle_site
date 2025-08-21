from flask import Blueprint, request, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from flask_login import current_user, login_required
from datetime import datetime, timezone
from .models import User, Puzzle, Hint, Issue, Submission
from .forms import PuzzleForm, HintForm, IssueForm
from . import db
from .admin_utils import admin_required
from app.puzzles import normalize_answer
from .email import notify_all_users_new_issue

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
        
        # Send email notifications to users who want them
        try:
            if new_issue.available_date <= datetime.now(timezone.utc):
                notify_all_users_new_issue(new_issue)
                flash('Issue created successfully and notifications sent!')
            else:
                flash('Issue created successfully! Notifications will be sent when the issue becomes available.')
        except Exception as e:
            flash('Issue created successfully, but failed to send some notifications.')
            print(f"Failed to send issue notifications: {e}")
        
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

@admin_bp.route('/puzzles')
@login_required
@admin_required
def puzzle_list():
    puzzles = Puzzle.query.all()
    return render_template('admin_puzzle_list.html', puzzles=puzzles)

@admin_bp.route('/issues')
@login_required
@admin_required
def issue_list():
    issues = Issue.query.all()
    return render_template('admin_issue_list.html', issues=issues)

@admin_bp.route('/hints')
@login_required
@admin_required
def hint_list():
    hints = Hint.query.all()
    return render_template('admin_hint_list.html', hints=hints)

@admin_bp.route('/delete_puzzle/<int:puzzle_id>')
@login_required
@admin_required
def delete_puzzle(puzzle_id):
    puzzle = Puzzle.query.get_or_404(puzzle_id)
    db.session.delete(puzzle)
    db.session.commit()
    flash("Puzzle deleted successfully.")
    return redirect(url_for('admin.puzzle_list'))

@admin_bp.route('/delete_issue/<int:issue_id>')
@login_required
@admin_required
def delete_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    db.session.delete(issue)
    db.session.commit()
    flash("Issue deleted successfully.")
    return redirect(url_for('admin.issue_list'))

@admin_bp.route('/delete_hint/<int:hint_id>')
@login_required
@admin_required
def delete_hint(hint_id):
    hint = Hint.query.get_or_404(hint_id)
    db.session.delete(hint)
    db.session.commit()
    flash("Hint deleted successfully.")
    return redirect(url_for('admin.hint_list'))

@admin_bp.route('/edit_puzzle/<int:puzzle_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_puzzle(puzzle_id):
    puzzle = Puzzle.query.get_or_404(puzzle_id)
    form = PuzzleForm(obj=puzzle)
    form.issue_id.choices = [(0, '-- No Issue --')] + [
        (i.id, i.title) for i in Issue.query.order_by(Issue.id).all()
    ]
    
    if request.method == 'GET':
        form.issue_id.data = puzzle.issue_id if puzzle.issue_id else 0
        form.answer.data = ''
    
    if form.validate_on_submit():
        puzzle.title = form.title.data
        puzzle.description = form.description.data
        puzzle.issue_id = form.issue_id.data if form.issue_id.data != 0 else None
        
        if form.answer.data:
            puzzle.answer_hash = generate_password_hash(normalize_answer(form.answer.data))
        
        db.session.commit()
        flash('Puzzle updated successfully!')
        return redirect(url_for('admin.puzzle_list'))
    
    return render_template('admin_edit_puzzle.html', form=form, puzzle=puzzle)

@admin_bp.route('/edit_issue/<int:issue_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    form = IssueForm(obj=issue)
    
    if form.validate_on_submit():
        issue.title = form.title.data
        issue.description = form.description.data
        issue.pdf_filename = form.pdf_filename.data or None
        issue.available_date = form.available_date.data
        
        db.session.commit()
        flash('Issue updated successfully!')
        return redirect(url_for('admin.issue_list'))
    
    return render_template('admin_edit_issue.html', form=form, issue=issue)

@admin_bp.route('/edit_hint/<int:hint_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_hint(hint_id):
    hint = Hint.query.get_or_404(hint_id)
    form = HintForm(obj=hint)
    form.puzzle_id.choices = [(p.id, p.title) for p in Puzzle.query.order_by(Puzzle.id).all()]
    
    if form.validate_on_submit():
        hint.puzzle_id = form.puzzle_id.data
        hint.hint_text = form.hint_text.data
        hint.unlock_date = form.unlock_date.data
        
        db.session.commit()
        flash('Hint updated successfully!')
        return redirect(url_for('admin.hint_list'))
    
    return render_template('admin_edit_hint.html', form=form, hint=hint)

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_puzzles': Puzzle.query.count(),
        'total_issues': Issue.query.count(),
        'total_submissions': Submission.query.count(),
        'correct_submissions': Submission.query.filter_by(is_correct=True).count(),
        'recent_users': User.query.order_by(User.id.desc()).limit(5).all(),
        'recent_submissions': Submission.query.order_by(Submission.submitted_at.desc()).limit(5).all()
    }
    return render_template('admin_dashboard.html', stats=stats)



bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('puzzle.list_issues'))  # or wherever you want logged-in users to land
    else:
        return redirect(url_for('auth.login'))  # or render a public landing page