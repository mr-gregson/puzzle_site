# Admin Operations Guide - Command Line Reference

This guide provides command-line operations for administrators to manage the Puzzle Site in production.

## 🔐 Container Access

### Finding Your Container
```bash
# List all running containers
docker ps

# Find puzzle site container specifically
docker ps | grep puzzle

# Get container name/ID
CONTAINER=$(docker ps --filter "ancestor=puzzle-site" --format "{{.Names}}" | head -1)
echo $CONTAINER
```

### Accessing the Application Container
```bash
# Interactive shell access
docker exec -it <container-name> /bin/bash

# Or using container ID
docker exec -it <container-id> /bin/bash

# One-liner to get shell in puzzle container
docker exec -it $(docker ps --filter "ancestor=puzzle-site" --format "{{.Names}}" | head -1) /bin/bash
```

## 👥 User Management

### Creating Admin Users
```bash
# Access container shell
docker exec -it <container-name> /bin/bash

# Run Python shell inside container
python -c "
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Create new admin user
    admin = User(
        username='admin',
        email='admin@company.com',
        display_name='System Administrator',
        password_hash=generate_password_hash('secure_password_here'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print('Admin user created successfully')
"
```

### Promoting User to Admin
```bash
# Interactive Python session in container
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    # Find user by username or email
    user = User.query.filter_by(username='username_here').first()
    # or: user = User.query.filter_by(email='user@email.com').first()
    
    if user:
        user.is_admin = True
        db.session.commit()
        print(f'User {user.username} promoted to admin')
    else:
        print('User not found')
"
```

### Listing All Users
```bash
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print(f'Total users: {len(users)}')
    print('ID | Username | Email | Admin | Display Name')
    print('-' * 60)
    for user in users:
        admin_status = 'Yes' if user.is_admin else 'No'
        print(f'{user.id:2} | {user.username:15} | {user.email:25} | {admin_status:5} | {user.display_name or \"N/A\"}')
"
```

### Disabling/Enabling Users
```bash
# Note: The current model doesn't have an 'active' field
# To disable a user, you would need to change their password
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import secrets

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='username_to_disable').first()
    if user:
        # Generate a random password they don't know
        user.password_hash = generate_password_hash(secrets.token_hex(32))
        db.session.commit()
        print(f'User {user.username} password reset (effectively disabled)')
"
```

## 🧩 Puzzle and Issue Management

### Creating New Issues
```bash
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import Issue
from datetime import datetime, timezone

app = create_app()
with app.app_context():
    issue = Issue(
        title='Monthly Challenge - January 2024',
        description='January puzzle collection with winter theme',
        pdf_filename='january_2024_puzzles.pdf',  # Optional
        available_date=datetime.now(timezone.utc)  # Adjust date as needed
    )
    db.session.add(issue)
    db.session.commit()
    print(f'Issue created with ID: {issue.id}')
"
```

### Creating New Puzzles
```bash
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import Puzzle
from werkzeug.security import generate_password_hash
from app.puzzles import normalize_answer

app = create_app()
with app.app_context():
    # Normalize and hash the answer
    answer = 'CORRECT ANSWER'
    normalized_answer = normalize_answer(answer)
    answer_hash = generate_password_hash(normalized_answer)
    
    puzzle = Puzzle(
        title='Sample Puzzle Title',
        description='This is a sample puzzle description with clues...',
        answer_hash=answer_hash,
        issue_id=1  # Link to existing issue, or None for standalone
    )
    db.session.add(puzzle)
    db.session.commit()
    print(f'Puzzle created with ID: {puzzle.id}')
"
```

### Adding Hints to Puzzles
```bash
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import Hint
from datetime import date, timedelta

app = create_app()
with app.app_context():
    hint = Hint(
        puzzle_id=1,  # Replace with actual puzzle ID
        hint_text='This is your first hint...',
        unlock_date=date.today() + timedelta(days=1)  # Available tomorrow
    )
    db.session.add(hint)
    db.session.commit()
    print(f'Hint created with ID: {hint.id}')
"
```

### Listing Puzzles and Progress
```bash
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import Puzzle, Submission, Issue

app = create_app()
with app.app_context():
    puzzles = Puzzle.query.all()
    print(f'Total puzzles: {len(puzzles)}')
    print('ID | Title | Issue | Attempts | Solved | Success Rate')
    print('-' * 70)
    
    for puzzle in puzzles:
        total_attempts = Submission.query.filter_by(puzzle_id=puzzle.id).count()
        correct_attempts = Submission.query.filter_by(puzzle_id=puzzle.id, is_correct=True).count()
        success_rate = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        issue_title = puzzle.issue.title[:20] if puzzle.issue else 'Standalone'
        
        print(f'{puzzle.id:2} | {puzzle.title[:20]:20} | {issue_title:20} | {total_attempts:8} | {correct_attempts:6} | {success_rate:5.1f}%')
"
```

## 📊 System Statistics and Monitoring

### User Activity Statistics
```bash
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import User, Submission, Puzzle
from sqlalchemy import func

app = create_app()
with app.app_context():
    total_users = User.query.count()
    total_puzzles = Puzzle.query.count()
    total_submissions = Submission.query.count()
    correct_submissions = Submission.query.filter_by(is_correct=True).count()
    
    print(f'=== SYSTEM STATISTICS ===')
    print(f'Total Users: {total_users}')
    print(f'Total Puzzles: {total_puzzles}')
    print(f'Total Submissions: {total_submissions}')
    print(f'Correct Submissions: {correct_submissions}')
    print(f'Overall Success Rate: {(correct_submissions/total_submissions*100):.1f}%' if total_submissions > 0 else 'No submissions yet')
    
    # Most active users
    print(f'\\n=== TOP 10 MOST ACTIVE USERS ===')
    active_users = db.session.query(
        User.username, 
        func.count(Submission.id).label('submission_count')
    ).join(Submission).group_by(User.id).order_by(func.count(Submission.id).desc()).limit(10).all()
    
    for user, count in active_users:
        print(f'{user:20} | {count:3} submissions')
"
```

### Puzzle Difficulty Analysis
```bash
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import Puzzle, Submission
from sqlalchemy import func

app = create_app()
with app.app_context():
    puzzle_stats = db.session.query(
        Puzzle.title,
        func.count(Submission.id).label('total_attempts'),
        func.sum(func.cast(Submission.is_correct, db.Integer)).label('correct_attempts')
    ).outerjoin(Submission).group_by(Puzzle.id).all()
    
    print('=== PUZZLE DIFFICULTY ANALYSIS ===')
    print('Title | Attempts | Solved | Success Rate | Difficulty')
    print('-' * 70)
    
    for title, attempts, correct in puzzle_stats:
        attempts = attempts or 0
        correct = correct or 0
        success_rate = (correct / attempts * 100) if attempts > 0 else 0
        
        if success_rate >= 80:
            difficulty = 'Easy'
        elif success_rate >= 50:
            difficulty = 'Medium'
        elif success_rate >= 20:
            difficulty = 'Hard'
        else:
            difficulty = 'Very Hard'
            
        print(f'{title[:20]:20} | {attempts:8} | {correct:6} | {success_rate:5.1f}% | {difficulty}')
"
```

## 🗄️ Database Operations

### Database Backup
```bash
# For PostgreSQL
docker exec <db-container-name> pg_dump -U puzzleuser puzzlesite > puzzle_backup_$(date +%Y%m%d).sql

# For MySQL
docker exec <db-container-name> mysqldump -u puzzleuser -p puzzlesite > puzzle_backup_$(date +%Y%m%d).sql
```

### Database Restore
```bash
# For PostgreSQL
docker exec -i <db-container-name> psql -U puzzleuser puzzlesite < puzzle_backup_20240115.sql

# For MySQL
docker exec -i <db-container-name> mysql -u puzzleuser -p puzzlesite < puzzle_backup_20240115.sql
```

### Manual Database Queries
```bash
# Access database directly
docker exec -it <db-container-name> psql -U puzzleuser puzzlesite

# Common queries:
# SELECT COUNT(*) FROM "user";
# SELECT username, email, is_admin FROM "user" WHERE is_admin = true;
# SELECT title, COUNT(submissions.id) as attempts FROM puzzle LEFT JOIN submission ON puzzle.id = submission.puzzle_id GROUP BY puzzle.id;
```

## 📧 Email Operations

### Test Email Configuration
```bash
# Test email sending
docker exec -it <container-name> python test_email.py

# Test with specific recipient
docker exec -it <container-name> python -c "
from app.email import send_welcome_email
from app.models import User
from app import create_app

app = create_app()
with app.app_context():
    # Test email to admin
    admin = User.query.filter_by(is_admin=True).first()
    if admin:
        try:
            send_welcome_email(admin)
            print('Test email sent successfully')
        except Exception as e:
            print(f'Email failed: {e}')
"
```

### Send Bulk Notifications (Use Carefully)
```bash
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import User
from app.email import send_welcome_email  # or create custom email function

app = create_app()
with app.app_context():
    # Example: Send notification to all users who opted in
    users = User.query.filter_by(email_notifications=True).all()
    
    print(f'Sending notifications to {len(users)} users...')
    for user in users:
        try:
            # Replace with your notification function
            # send_custom_notification(user, 'Subject', 'Message')
            print(f'Would send to: {user.email}')
        except Exception as e:
            print(f'Failed to send to {user.email}: {e}')
    
    print('Bulk notification complete')
"
```

## 📁 File Management

### Managing PDF Files
```bash
# List uploaded PDFs
docker exec -it <container-name> ls -la /app/app/static/pdfs/

# Copy PDF into container
docker cp local_puzzle.pdf <container-name>:/app/app/static/pdfs/

# Copy PDF out of container
docker cp <container-name>:/app/app/static/pdfs/puzzle.pdf ./local_puzzle.pdf
```

### Log Management
```bash
# View application logs
docker exec -it <container-name> tail -f /app/logs/puzzle_site.log

# View last 100 log entries
docker exec -it <container-name> tail -100 /app/logs/puzzle_site.log

# Search logs for errors
docker exec -it <container-name> grep -i error /app/logs/puzzle_site.log

# Rotate logs (if they get too large)
docker exec -it <container-name> bash -c "mv /app/logs/puzzle_site.log /app/logs/puzzle_site.log.old && touch /app/logs/puzzle_site.log"
```

## 🚨 Emergency Operations

### Application Health Check
```bash
# Quick health check
curl http://your-domain.com/health

# Detailed health check
curl http://your-domain.com/health/detailed

# Check from inside container
docker exec -it <container-name> curl http://localhost:8000/health
```

### Restart Application
```bash
# Restart container
docker restart <container-name>

# Or with docker-compose
docker-compose restart web

# Or in Kubernetes
kubectl rollout restart deployment puzzle-site
```

### View Container Logs
```bash
# Recent logs
docker logs --tail 100 <container-name>

# Follow logs in real-time
docker logs -f <container-name>

# Logs with timestamps
docker logs -t <container-name>
```

### Emergency User Password Reset
```bash
docker exec -it <container-name> python -c "
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='user@email.com').first()
    if user:
        new_password = 'TempPassword123!'
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print(f'Password reset for {user.username}')
        print(f'Temporary password: {new_password}')
        print('User should change this password immediately')
    else:
        print('User not found')
"
```

## 📝 Maintenance Routines

### Weekly Maintenance Script
```bash
#!/bin/bash
# Save as maintenance.sh

CONTAINER_NAME="puzzle-site-container"
DATE=$(date +%Y%m%d)

echo "=== Weekly Puzzle Site Maintenance - $DATE ==="

# 1. Backup database
echo "Creating database backup..."
docker exec puzzle-db pg_dump -U puzzleuser puzzlesite > "backups/puzzle_backup_$DATE.sql"

# 2. Check application health
echo "Checking application health..."
docker exec $CONTAINER_NAME curl -s http://localhost:8000/health/detailed

# 3. Generate user statistics
echo "Generating user statistics..."
docker exec -it $CONTAINER_NAME python -c "
from app import create_app, db
from app.models import User, Submission
app = create_app()
with app.app_context():
    total_users = User.query.count()
    active_users = User.query.join(Submission).distinct().count()
    print(f'Total users: {total_users}, Active users: {active_users}')
"

# 4. Clean old logs (keep last 30 days)
echo "Cleaning old logs..."
find logs/ -name "*.log.*" -mtime +30 -delete

echo "Maintenance complete"
```

## 🔧 Troubleshooting Quick Reference

### Common Issues and Solutions

**Container won't start:**
```bash
docker logs <container-name>  # Check startup logs
docker exec -it <container-name> env  # Check environment variables
```

**Database connection issues:**
```bash
docker exec -it <container-name> ping <database-host>
docker exec -it <container-name> python -c "from app import db; print(db.engine.url)"
```

**Email not working:**
```bash
docker exec -it <container-name> python test_email.py
```

**High memory usage:**
```bash
docker stats <container-name>  # Monitor resource usage
docker exec -it <container-name> ps aux  # Check processes
```

---

## 🔐 Security Reminders

- **Always use strong passwords** when creating admin accounts
- **Backup regularly** and test your backups
- **Monitor logs** for suspicious activity
- **Keep container images updated** with security patches
- **Limit access** to production containers
- **Use secure connections** (SSH, VPN) when accessing production systems

**Emergency Contact**: [Your contact information]
**Documentation**: See `IT_DEPLOYMENT_GUIDE.md` for additional technical details