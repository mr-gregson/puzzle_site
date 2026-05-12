from sqlalchemy import and_, case, distinct, func

from . import db
from .models import Issue, Puzzle, Submission, User


def _safe_percentage(numerator, denominator):
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * 100


def get_admin_dashboard_reporting_summary(limit=5):
    solved_count_expr = func.count(
        distinct(case((Submission.is_correct == True, Submission.user_id), else_=None))
    )

    top_solved = (
        db.session.query(
            Puzzle.id,
            Puzzle.title,
            solved_count_expr.label("solve_count"),
        )
        .outerjoin(Submission, Submission.puzzle_id == Puzzle.id)
        .group_by(Puzzle.id, Puzzle.title)
        .order_by(solved_count_expr.desc(), Puzzle.title.asc())
        .limit(limit)
        .all()
    )

    top_users = (
        db.session.query(
            User.id,
            User.username,
            func.count(
                distinct(case((Submission.is_correct == True, Submission.puzzle_id), else_=None))
            ).label("solved_puzzles"),
        )
        .outerjoin(Submission, Submission.user_id == User.id)
        .group_by(User.id, User.username)
        .order_by(func.count(distinct(case((Submission.is_correct == True, Submission.puzzle_id), else_=None))).desc(), User.username.asc())
        .limit(limit)
        .all()
    )

    unsolved_puzzles = (
        db.session.query(Puzzle.id, Puzzle.title)
        .outerjoin(
            Submission,
            and_(Submission.puzzle_id == Puzzle.id, Submission.is_correct == True),
        )
        .group_by(Puzzle.id, Puzzle.title)
        .having(func.count(Submission.id) == 0)
        .order_by(Puzzle.title.asc())
        .limit(limit)
        .all()
    )

    return {
        "top_solved_puzzles": top_solved,
        "top_users": top_users,
        "unsolved_puzzles": unsolved_puzzles,
    }


def get_puzzle_report_rows(issue_id=None, sort="most_solved"):
    solve_count_expr = func.count(
        distinct(case((Submission.is_correct == True, Submission.user_id), else_=None))
    )
    attempts_expr = func.count(Submission.id)
    correct_submissions_expr = func.sum(case((Submission.is_correct == True, 1), else_=0))

    query = (
        db.session.query(
            Puzzle.id.label("puzzle_id"),
            Puzzle.title.label("puzzle_title"),
            Issue.id.label("issue_id"),
            Issue.title.label("issue_title"),
            solve_count_expr.label("solve_count"),
            attempts_expr.label("attempt_count"),
            correct_submissions_expr.label("correct_submission_count"),
        )
        .outerjoin(Issue, Puzzle.issue_id == Issue.id)
        .outerjoin(Submission, Submission.puzzle_id == Puzzle.id)
        .group_by(Puzzle.id, Puzzle.title, Issue.id, Issue.title)
    )

    if issue_id:
        query = query.filter(Puzzle.issue_id == issue_id)

    if sort == "least_solved":
        query = query.order_by(solve_count_expr.asc(), Puzzle.title.asc())
    elif sort == "most_attempted":
        query = query.order_by(attempts_expr.desc(), Puzzle.title.asc())
    elif sort == "title":
        query = query.order_by(Puzzle.title.asc())
    else:
        query = query.order_by(solve_count_expr.desc(), Puzzle.title.asc())

    rows = query.all()

    return [
        {
            "puzzle_id": row.puzzle_id,
            "puzzle_title": row.puzzle_title,
            "issue_id": row.issue_id,
            "issue_title": row.issue_title,
            "solve_count": int(row.solve_count or 0),
            "attempt_count": int(row.attempt_count or 0),
            "correct_submission_count": int(row.correct_submission_count or 0),
            "success_rate": _safe_percentage(
                int(row.correct_submission_count or 0),
                int(row.attempt_count or 0),
            ),
        }
        for row in rows
    ]


def get_puzzle_solver_rows(puzzle_id):
    puzzle = Puzzle.query.get_or_404(puzzle_id)

    first_correct_subq = (
        db.session.query(
            Submission.user_id.label("user_id"),
            func.min(Submission.submitted_at).label("first_correct_at"),
        )
        .filter(Submission.puzzle_id == puzzle_id, Submission.is_correct == True)
        .group_by(Submission.user_id)
        .subquery()
    )

    solver_stats_query = (
        db.session.query(
            User.id.label("user_id"),
            User.username.label("username"),
            first_correct_subq.c.first_correct_at.label("first_correct_at"),
            func.count(Submission.id).label("attempt_count"),
            func.sum(case((Submission.is_correct == True, 1), else_=0)).label("correct_submission_count"),
            func.sum(
                case(
                    (
                        and_(
                            Submission.is_correct == False,
                            Submission.submitted_at < first_correct_subq.c.first_correct_at,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("incorrect_before_solve"),
        )
        .join(first_correct_subq, first_correct_subq.c.user_id == User.id)
        .join(
            Submission,
            and_(Submission.user_id == User.id, Submission.puzzle_id == puzzle_id),
        )
        .group_by(User.id, first_correct_subq.c.first_correct_at)
        .order_by(first_correct_subq.c.first_correct_at.asc(), User.username.asc())
    )

    rows = solver_stats_query.all()

    return puzzle, [
        {
            "user_id": row.user_id,
            "username": row.username,
            "first_correct_at": row.first_correct_at,
            "attempt_count": int(row.attempt_count or 0),
            "correct_submission_count": int(row.correct_submission_count or 0),
            "incorrect_before_solve": int(row.incorrect_before_solve or 0),
        }
        for row in rows
    ]


def get_user_report_rows(sort="most_solved"):
    solved_count_expr = func.count(
        distinct(case((Submission.is_correct == True, Submission.puzzle_id), else_=None))
    )
    attempts_expr = func.count(Submission.id)
    correct_submissions_expr = func.sum(case((Submission.is_correct == True, 1), else_=0))

    query = (
        db.session.query(
            User.id.label("user_id"),
            User.username.label("username"),
            User.email.label("email"),
            solved_count_expr.label("solved_puzzles"),
            attempts_expr.label("attempt_count"),
            correct_submissions_expr.label("correct_submission_count"),
        )
        .outerjoin(Submission, Submission.user_id == User.id)
        .group_by(User.id, User.username, User.email)
    )

    if sort == "most_attempted":
        query = query.order_by(attempts_expr.desc(), User.username.asc())
    elif sort == "username":
        query = query.order_by(User.username.asc())
    else:
        query = query.order_by(solved_count_expr.desc(), User.username.asc())

    rows = query.all()

    return [
        {
            "user_id": row.user_id,
            "username": row.username,
            "email": row.email,
            "solved_puzzles": int(row.solved_puzzles or 0),
            "attempt_count": int(row.attempt_count or 0),
            "correct_submission_count": int(row.correct_submission_count or 0),
            "success_rate": _safe_percentage(
                int(row.correct_submission_count or 0),
                int(row.attempt_count or 0),
            ),
        }
        for row in rows
    ]


def get_user_issue_progress_rows(user_id=None, issue_id=None, sort="best_completion"):
    issue_query = (
        db.session.query(
            Issue.id.label("issue_id"),
            Issue.title.label("issue_title"),
            func.count(Puzzle.id).label("total_puzzles"),
        )
        .outerjoin(Puzzle, Puzzle.issue_id == Issue.id)
        .group_by(Issue.id, Issue.title)
        .order_by(Issue.title.asc())
    )

    if issue_id:
        issue_query = issue_query.filter(Issue.id == issue_id)

    issues = issue_query.all()

    user_query = db.session.query(User.id.label("user_id"), User.username.label("username")).order_by(User.username.asc())
    if user_id:
        user_query = user_query.filter(User.id == user_id)

    users = user_query.all()

    solved_pairs_query = (
        db.session.query(
            Submission.user_id.label("user_id"),
            Puzzle.issue_id.label("issue_id"),
            Submission.puzzle_id.label("puzzle_id"),
        )
        .join(Puzzle, Puzzle.id == Submission.puzzle_id)
        .filter(Submission.is_correct == True, Puzzle.issue_id.isnot(None))
        .group_by(Submission.user_id, Puzzle.issue_id, Submission.puzzle_id)
    )

    if user_id:
        solved_pairs_query = solved_pairs_query.filter(Submission.user_id == user_id)
    if issue_id:
        solved_pairs_query = solved_pairs_query.filter(Puzzle.issue_id == issue_id)

    solved_pairs_subq = solved_pairs_query.subquery()

    solved_counts = (
        db.session.query(
            solved_pairs_subq.c.user_id,
            solved_pairs_subq.c.issue_id,
            func.count(solved_pairs_subq.c.puzzle_id).label("solved_count"),
        )
        .group_by(solved_pairs_subq.c.user_id, solved_pairs_subq.c.issue_id)
        .all()
    )

    solved_map = {
        (row.user_id, row.issue_id): int(row.solved_count or 0)
        for row in solved_counts
    }

    rows = []
    for user_row in users:
        for issue_row in issues:
            total_puzzles = int(issue_row.total_puzzles or 0)
            if total_puzzles == 0:
                continue

            solved_count = solved_map.get((user_row.user_id, issue_row.issue_id), 0)
            rows.append(
                {
                    "user_id": user_row.user_id,
                    "username": user_row.username,
                    "issue_id": issue_row.issue_id,
                    "issue_title": issue_row.issue_title,
                    "solved_count": solved_count,
                    "total_puzzles": total_puzzles,
                    "completion_rate": _safe_percentage(solved_count, total_puzzles),
                }
            )

    if sort == "least_completion":
        rows.sort(key=lambda row: (row["completion_rate"], row["username"], row["issue_title"]))
    elif sort == "username":
        rows.sort(key=lambda row: (row["username"], -row["completion_rate"], row["issue_title"]))
    elif sort == "issue":
        rows.sort(key=lambda row: (row["issue_title"], -row["completion_rate"], row["username"]))
    else:
        rows.sort(key=lambda row: (-row["completion_rate"], row["username"], row["issue_title"]))

    return rows
