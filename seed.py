# seed.py
from app import create_app, db
from app.models import User, Issue, Puzzle, Hint
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, timezone

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # --- Create users ---
    user1 = User(
        username="user1",
        display_name="Alice",
        email="alice@example.com",
        password_hash=generate_password_hash("password"),
        is_admin=False
    )
    admin = User(
        username="admin",
        display_name="Admin",
        email="admin@example.com",
        password_hash=generate_password_hash("adminpass"),
        is_admin=True
    )

    # --- Create issues ---
    issue1 = Issue(
        title="Issue 1: Summer Edition",
        description="A set of summer-themed puzzles.",
        available_date=datetime.now(timezone.utc) - timedelta(days=1),
        pdf_filename="issue1.pdf"
    )
    issue2 = Issue(
        title="Issue 2: Hidden Future",
        description="Available next week.",
        available_date=datetime.now(timezone.utc) + timedelta(days=7),
        pdf_filename="issue2.pdf"
    )

    # --- Create puzzles ---
    puzzle1 = Puzzle(
        title="Riddle of the Sphinx",
        description="What walks on four legs in the morning...",
        answer_hash=generate_password_hash("aman"),
        issue=issue1
    )
    puzzle2 = Puzzle(
        title="Reverse Me",
        description="What word becomes shorter when you add two letters?",
        answer_hash=generate_password_hash("short"),
        issue=issue1
    )

    # --- Create hints ---
    hint1 = Hint(
        puzzle=puzzle1,
        hint_text="Think of life stages.",
        unlock_date=datetime.now(timezone.utc) - timedelta(days=1)
    )
    hint2 = Hint(
        puzzle=puzzle2,
        hint_text="It’s a play on the word itself.",
        unlock_date=datetime.now(timezone.utc) + timedelta(days=2)
    )

    db.session.add_all([user1, admin, issue1, issue2, puzzle1, puzzle2, hint1, hint2])
    db.session.commit()

    print("✅ Database seeded with test data.")
    
    # seed.py (end of file)
    # Fix any naive datetime fields in Issue objects
    for issue in Issue.query.all():
        print(f"Issue: {issue.title}, tzinfo: {issue.available_date.tzinfo}")
        if issue.available_date and issue.available_date.tzinfo is None:
            issue.available_date = issue.available_date.replace(tzinfo=timezone.utc)
            print(f"→ Fixed tz for {issue.title}, tzinfo: {issue.available_date.tzinfo} (should be UTC)")

    db.session.commit()
    print("✅ Database seeded and issue dates fixed to be timezone-aware.")

