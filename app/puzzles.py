from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .models import Puzzle, Submission, Hint, Issue
from .forms import AnswerForm
from . import db
from datetime import date, datetime, timezone
from werkzeug.security import check_password_hash
import string
from .utils import compare_dates

def normalize_answer(text):
            # Lowercase, remove punctuation and spaces
            return ''.join(
                c for c in text.lower() if c not in string.punctuation and not c.isspace()
            )

puzzle_bp = Blueprint('puzzle', __name__)

@puzzle_bp.route('/issues')
@login_required
def list_issues():
    issues = Issue.query.order_by(Issue.available_date).all()
    current_time = datetime.now(timezone.utc)
    
    issue_progress = []
    for issue in issues:
        puzzle_count = len(issue.puzzles)
        solved_count = 0
        
        if puzzle_count > 0:
            puzzle_ids = [p.id for p in issue.puzzles]
            solved_count = Submission.query.filter(
                Submission.user_id == current_user.id,
                Submission.puzzle_id.in_(puzzle_ids),
                Submission.is_correct == True
            ).count()
        
        progress_percentage = (solved_count / puzzle_count * 100) if puzzle_count > 0 else 0
        
        issue_progress.append({
            'issue': issue,
            'puzzle_count': puzzle_count,
            'solved_count': solved_count,
            'progress_percentage': progress_percentage
        })
    
    return render_template('issue_list.html', issue_progress=issue_progress, current_time=current_time)


@puzzle_bp.route('/issue/<int:issue_id>')
@login_required
def issue_detail(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    now = datetime.now(timezone.utc)
    
    if compare_dates(now, issue.available_date):
        return render_template('issue_locked.html', issue=issue)

    puzzles = issue.puzzles
    correct_subs = Submission.query.filter(
        Submission.user_id == current_user.id,
        Submission.puzzle_id.in_([p.id for p in puzzles]),
        Submission.is_correct == True
    ).all()
    solved_lookup = {sub.puzzle_id: sub for sub in correct_subs}

    return render_template(
        'issue_detail.html',
        issue=issue,
        solved_lookup=solved_lookup
    )


@puzzle_bp.route('/puzzles')
@login_required
def list_puzzles():
    puzzles = Puzzle.query.all()
    return render_template('puzzle_list.html', puzzles=puzzles)

@puzzle_bp.route('/puzzle/<int:puzzle_id>', methods=['GET', 'POST'])
@login_required
def puzzle_detail(puzzle_id):
    puzzle = Puzzle.query.get_or_404(puzzle_id)
    
    issue = puzzle.issue
    now = datetime.now(timezone.utc)

    if issue and compare_dates(now, issue.available_date):
        flash(f"🕒 This puzzle is part of '{issue.title}', which will be available on {issue.available_date.strftime('%B %d, %Y')}.")
        return redirect(url_for('puzzle.list_issues'))
    
    form = AnswerForm()
    user_submission = Submission.query.filter_by(
        user_id=current_user.id, puzzle_id=puzzle_id, is_correct=True
    ).first()

    if form.validate_on_submit() and not user_submission:

        submitted_raw = form.answer.data
        submitted = normalize_answer(submitted_raw)
        correct = check_password_hash(puzzle.answer_hash, submitted)


        submission = Submission(
            user_id=current_user.id,
            puzzle_id=puzzle.id,
            submitted_answer=submitted_raw,
            is_correct=correct
        )
        db.session.add(submission)
        db.session.commit()

        if correct:
            flash(f"✅ '{submitted_raw}' is correct!")
        else:
            flash(f"❌ '{submitted_raw}' is incorrect.")

        return redirect(url_for('puzzle.puzzle_detail', puzzle_id=puzzle_id))

    unlocked_hints = Hint.query.filter(
        Hint.puzzle_id == puzzle_id,
        Hint.unlock_date <= date.today()
    ).order_by(Hint.unlock_date).all()

    return render_template(
        'puzzle_detail.html',
        puzzle=puzzle,
        form=form,
        unlocked_hints=unlocked_hints,
        correct=user_submission is not None
    )

@puzzle_bp.route('/dashboard')
@login_required
def user_dashboard():
    user_stats = {
        'total_submissions': Submission.query.filter_by(user_id=current_user.id).count(),
        'correct_submissions': Submission.query.filter_by(user_id=current_user.id, is_correct=True).count(),
        'total_puzzles': Puzzle.query.count(),
        'solved_puzzles': Submission.query.filter_by(user_id=current_user.id, is_correct=True).count(),
        'recent_submissions': Submission.query.filter_by(user_id=current_user.id).order_by(Submission.submitted_at.desc()).limit(10).all(),
        'recent_correct': Submission.query.filter_by(user_id=current_user.id, is_correct=True).order_by(Submission.submitted_at.desc()).limit(5).all(),
        'issues_progress': []
    }
    
    # Calculate success rate
    if user_stats['total_submissions'] > 0:
        user_stats['success_rate'] = (user_stats['correct_submissions'] / user_stats['total_submissions']) * 100
    else:
        user_stats['success_rate'] = 0
    
    # Calculate progress completion
    if user_stats['total_puzzles'] > 0:
        user_stats['completion_rate'] = (user_stats['solved_puzzles'] / user_stats['total_puzzles']) * 100
    else:
        user_stats['completion_rate'] = 0
    
    # Get issue-specific progress
    issues = Issue.query.all()
    for issue in issues:
        puzzle_count = len(issue.puzzles)
        if puzzle_count > 0:
            puzzle_ids = [p.id for p in issue.puzzles]
            solved_count = Submission.query.filter(
                Submission.user_id == current_user.id,
                Submission.puzzle_id.in_(puzzle_ids),
                Submission.is_correct == True
            ).count()
            
            user_stats['issues_progress'].append({
                'issue': issue,
                'total': puzzle_count,
                'solved': solved_count,
                'percentage': (solved_count / puzzle_count * 100) if puzzle_count > 0 else 0
            })
    
    return render_template('user_dashboard.html', stats=user_stats)