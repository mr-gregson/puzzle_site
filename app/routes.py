import csv
import io

from flask import Blueprint, Response, request, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from flask_login import current_user, login_required
from datetime import datetime, timezone
from .models import User, Puzzle, Hint, Issue, Submission, Erratum, PuzzleAnswerRule
from .forms import PuzzleForm, HintForm, IssueForm, ErrataForm, PuzzleAnswerRuleForm
from . import db
from .admin_utils import admin_required
from app.puzzles import normalize_answer
from .email import notify_all_users_new_issue
from .reporting import (
    get_admin_dashboard_reporting_summary,
    get_puzzle_report_rows,
    get_puzzle_solver_rows,
    get_user_issue_progress_rows,
    get_user_report_rows,
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _parse_optional_int(value):
    if value in (None, "", "0"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _csv_response(filename, headers, rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )

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
            answer_pdf_filename=form.answer_pdf_filename.data or None,
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

    return render_template('admin_add_issue.html', form=form)

@admin_bp.route('/add_puzzle', methods=['GET', 'POST'])
@login_required
@admin_required
def add_puzzle():
    form = PuzzleForm()
    form.issue_id.choices = [(0, '-- No Issue --')] + [
        (i.id, i.title) for i in Issue.query.order_by(Issue.id).all()
    ]

    if form.validate_on_submit():
        if not form.answer.data:
            flash('Answer is required when creating a puzzle.')
            return render_template('admin_add_puzzle.html', form=form)

        issue_id = form.issue_id.data if form.issue_id.data != 0 else None
        new_puzzle = Puzzle(
            title=form.title.data,
            description=form.description.data,
            answer_hash=generate_password_hash(normalize_answer(form.answer.data)),
            correct_response=form.correct_response.data or None,
            incorrect_response=form.incorrect_response.data or None,
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
        puzzle.correct_response = form.correct_response.data or None
        puzzle.incorrect_response = form.incorrect_response.data or None
        
        if form.answer.data:
            puzzle.answer_hash = generate_password_hash(normalize_answer(form.answer.data))
        
        db.session.commit()
        flash('Puzzle updated successfully!')
        return redirect(url_for('admin.puzzle_list'))
    
    return render_template('admin_edit_puzzle.html', form=form, puzzle=puzzle)


@admin_bp.route('/puzzle_response_rules/<int:puzzle_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def puzzle_response_rules(puzzle_id):
    puzzle = Puzzle.query.get_or_404(puzzle_id)
    form = PuzzleAnswerRuleForm()

    if form.validate_on_submit():
        normalized_answer = normalize_answer(form.answer.data)
        outcome = form.outcome.data

        if outcome == 'correct':
            is_correct_override = True
        elif outcome == 'incorrect':
            is_correct_override = False
        else:
            is_correct_override = None

        existing_rule = PuzzleAnswerRule.query.filter_by(
            puzzle_id=puzzle.id,
            answer_normalized=normalized_answer,
        ).first()

        if existing_rule:
            existing_rule.feedback_text = form.feedback_text.data or None
            existing_rule.is_correct_override = is_correct_override
            flash('Response rule updated.')
        else:
            db.session.add(PuzzleAnswerRule(
                puzzle_id=puzzle.id,
                answer_normalized=normalized_answer,
                feedback_text=form.feedback_text.data or None,
                is_correct_override=is_correct_override,
            ))
            flash('Response rule added.')

        db.session.commit()
        return redirect(url_for('admin.puzzle_response_rules', puzzle_id=puzzle.id))

    rules = PuzzleAnswerRule.query.filter_by(puzzle_id=puzzle.id).order_by(PuzzleAnswerRule.created_at.desc()).all()
    return render_template(
        'admin_puzzle_response_rules.html',
        puzzle=puzzle,
        form=form,
        rules=rules,
    )


@admin_bp.route('/delete_puzzle_response_rule/<int:rule_id>')
@login_required
@admin_required
def delete_puzzle_response_rule(rule_id):
    rule = PuzzleAnswerRule.query.get_or_404(rule_id)
    puzzle_id = rule.puzzle_id
    db.session.delete(rule)
    db.session.commit()
    flash('Response rule deleted.')
    return redirect(url_for('admin.puzzle_response_rules', puzzle_id=puzzle_id))

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
        issue.answer_pdf_filename = form.answer_pdf_filename.data or None
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

@admin_bp.route('/errata')
@login_required
@admin_required
def errata_list():
    errata = Erratum.query.order_by(Erratum.created_at.desc()).all()
    return render_template('admin_errata_list.html', errata=errata)

@admin_bp.route('/add_erratum', methods=['GET', 'POST'])
@login_required
@admin_required
def add_erratum():
    form = ErrataForm()
    form.puzzle_id.choices = [(0, '-- No Puzzle --')] + [
        (p.id, p.title) for p in Puzzle.query.order_by(Puzzle.title).all()
    ]
    form.issue_id.choices = [(0, '-- No Issue --')] + [
        (i.id, i.title) for i in Issue.query.order_by(Issue.title).all()
    ]

    if form.validate_on_submit():
        puzzle_id = form.puzzle_id.data if form.puzzle_id.data != 0 else None
        issue_id = form.issue_id.data if form.issue_id.data != 0 else None
        
        new_erratum = Erratum(
            title=form.title.data,
            description=form.description.data,
            puzzle_id=puzzle_id,
            issue_id=issue_id,
            is_active=form.is_active.data
        )
        db.session.add(new_erratum)
        db.session.commit()
        flash('Erratum created successfully!')
        return redirect(url_for('admin.errata_list'))

    return render_template('admin_add_erratum.html', form=form)

@admin_bp.route('/edit_erratum/<int:erratum_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_erratum(erratum_id):
    erratum = Erratum.query.get_or_404(erratum_id)
    form = ErrataForm(obj=erratum)
    
    form.puzzle_id.choices = [(0, '-- No Puzzle --')] + [
        (p.id, p.title) for p in Puzzle.query.order_by(Puzzle.title).all()
    ]
    form.issue_id.choices = [(0, '-- No Issue --')] + [
        (i.id, i.title) for i in Issue.query.order_by(Issue.title).all()
    ]
    
    if request.method == 'GET':
        form.puzzle_id.data = erratum.puzzle_id if erratum.puzzle_id else 0
        form.issue_id.data = erratum.issue_id if erratum.issue_id else 0
    
    if form.validate_on_submit():
        erratum.title = form.title.data
        erratum.description = form.description.data
        erratum.puzzle_id = form.puzzle_id.data if form.puzzle_id.data != 0 else None
        erratum.issue_id = form.issue_id.data if form.issue_id.data != 0 else None
        erratum.is_active = form.is_active.data
        
        db.session.commit()
        flash('Erratum updated successfully!')
        return redirect(url_for('admin.errata_list'))
    
    return render_template('admin_edit_erratum.html', form=form, erratum=erratum)

@admin_bp.route('/delete_erratum/<int:erratum_id>')
@login_required
@admin_required
def delete_erratum(erratum_id):
    erratum = Erratum.query.get_or_404(erratum_id)
    db.session.delete(erratum)
    db.session.commit()
    flash("Erratum deleted successfully.")
    return redirect(url_for('admin.errata_list'))


@admin_bp.route('/reports')
@login_required
@admin_required
def reports_index():
    return render_template('admin_reports.html')


@admin_bp.route('/reports/puzzles')
@login_required
@admin_required
def report_puzzles():
    selected_issue_id = _parse_optional_int(request.args.get('issue_id'))
    selected_sort = request.args.get('sort', 'most_solved')

    issues = Issue.query.order_by(Issue.title.asc()).all()
    puzzle_rows = get_puzzle_report_rows(issue_id=selected_issue_id, sort=selected_sort)

    return render_template(
        'admin_report_puzzles.html',
        puzzle_rows=puzzle_rows,
        issues=issues,
        selected_issue_id=selected_issue_id,
        selected_sort=selected_sort,
    )


@admin_bp.route('/reports/puzzles/export')
@login_required
@admin_required
def report_puzzles_export():
    selected_issue_id = _parse_optional_int(request.args.get('issue_id'))
    selected_sort = request.args.get('sort', 'most_solved')

    puzzle_rows = get_puzzle_report_rows(issue_id=selected_issue_id, sort=selected_sort)
    rows = [
        [
            row['puzzle_id'],
            row['puzzle_title'],
            row['issue_title'] or 'Unassigned',
            row['solve_count'],
            row['attempt_count'],
            row['correct_submission_count'],
            f"{row['success_rate']:.1f}",
        ]
        for row in puzzle_rows
    ]

    return _csv_response(
        'puzzle-report.csv',
        ['Puzzle ID', 'Puzzle Title', 'Issue', 'Solvers', 'Attempts', 'Correct Submissions', 'Success Rate %'],
        rows,
    )


@admin_bp.route('/reports/puzzles/<int:puzzle_id>')
@login_required
@admin_required
def report_puzzle_detail(puzzle_id):
    puzzle, solver_rows = get_puzzle_solver_rows(puzzle_id)
    return render_template(
        'admin_report_puzzle_detail.html',
        puzzle=puzzle,
        solver_rows=solver_rows,
    )


@admin_bp.route('/reports/puzzles/<int:puzzle_id>/export')
@login_required
@admin_required
def report_puzzle_detail_export(puzzle_id):
    puzzle, solver_rows = get_puzzle_solver_rows(puzzle_id)
    rows = [
        [
            row['user_id'],
            row['username'],
            row['attempt_count'],
            row['correct_submission_count'],
            row['incorrect_before_solve'],
            row['first_correct_at'].strftime('%Y-%m-%d %H:%M:%S') if row['first_correct_at'] else '',
        ]
        for row in solver_rows
    ]

    return _csv_response(
        f"puzzle-{puzzle.id}-solvers.csv",
        ['User ID', 'Username', 'Attempts', 'Correct Submissions', 'Incorrect Before First Solve', 'First Correct Submission (UTC)'],
        rows,
    )


@admin_bp.route('/reports/users')
@login_required
@admin_required
def report_users():
    selected_sort = request.args.get('sort', 'most_solved')
    user_rows = get_user_report_rows(sort=selected_sort)
    return render_template(
        'admin_report_users.html',
        user_rows=user_rows,
        selected_sort=selected_sort,
    )


@admin_bp.route('/reports/users/export')
@login_required
@admin_required
def report_users_export():
    selected_sort = request.args.get('sort', 'most_solved')
    user_rows = get_user_report_rows(sort=selected_sort)
    rows = [
        [
            row['user_id'],
            row['username'],
            row['email'],
            row['solved_puzzles'],
            row['attempt_count'],
            row['correct_submission_count'],
            f"{row['success_rate']:.1f}",
        ]
        for row in user_rows
    ]

    return _csv_response(
        'user-report.csv',
        ['User ID', 'Username', 'Email', 'Solved Puzzles', 'Attempts', 'Correct Submissions', 'Success Rate %'],
        rows,
    )


@admin_bp.route('/reports/issue-progress')
@login_required
@admin_required
def report_issue_progress():
    selected_user_id = _parse_optional_int(request.args.get('user_id'))
    selected_issue_id = _parse_optional_int(request.args.get('issue_id'))
    selected_sort = request.args.get('sort', 'best_completion')

    users = User.query.order_by(User.username.asc()).all()
    issues = Issue.query.order_by(Issue.title.asc()).all()
    progress_rows = get_user_issue_progress_rows(
        user_id=selected_user_id,
        issue_id=selected_issue_id,
        sort=selected_sort,
    )

    return render_template(
        'admin_report_issue_progress.html',
        progress_rows=progress_rows,
        users=users,
        issues=issues,
        selected_user_id=selected_user_id,
        selected_issue_id=selected_issue_id,
        selected_sort=selected_sort,
    )


@admin_bp.route('/reports/issue-progress/export')
@login_required
@admin_required
def report_issue_progress_export():
    selected_user_id = _parse_optional_int(request.args.get('user_id'))
    selected_issue_id = _parse_optional_int(request.args.get('issue_id'))
    selected_sort = request.args.get('sort', 'best_completion')

    progress_rows = get_user_issue_progress_rows(
        user_id=selected_user_id,
        issue_id=selected_issue_id,
        sort=selected_sort,
    )
    rows = [
        [
            row['user_id'],
            row['username'],
            row['issue_id'],
            row['issue_title'],
            row['solved_count'],
            row['total_puzzles'],
            f"{row['completion_rate']:.1f}",
        ]
        for row in progress_rows
    ]

    return _csv_response(
        'issue-progress-report.csv',
        ['User ID', 'Username', 'Issue ID', 'Issue', 'Solved', 'Total Puzzles', 'Completion Rate %'],
        rows,
    )

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
        'total_distinct_solves': Submission.query.filter_by(is_correct=True).with_entities(Submission.user_id, Submission.puzzle_id).distinct().count(),
        'total_errata': Erratum.query.count(),
        'recent_users': User.query.order_by(User.id.desc()).limit(5).all(),
        'recent_submissions': Submission.query.order_by(Submission.submitted_at.desc()).limit(5).all(),
    }
    stats['reporting'] = get_admin_dashboard_reporting_summary(limit=5)
    return render_template('admin_dashboard.html', stats=stats)



bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('puzzle.list_issues'))  # or wherever you want logged-in users to land
    else:
        return redirect(url_for('auth.login'))  # or render a public landing page