# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
- **Start development server**: `python run.py`
- **Database setup**: `python seed.py` (drops and recreates database with test data)
- **Install dependencies**: `pip install -r requirements.txt`

### Database Operations
- The application uses SQLite database located at `instance/puzzle_site.db`
- Models are defined in `app/models.py`
- Database initialization and seeding is handled by `seed.py`

## Architecture Overview

This is a Flask web application for a puzzle/competition site with the following structure:

### Core Components
- **Flask App Factory**: `app/__init__.py` - Creates and configures the Flask application
- **Models**: `app/models.py` - SQLAlchemy models for User, Puzzle, Issue, Submission, Hint
- **Authentication**: `app/auth.py` - User registration, login, logout functionality
- **Main Routes**: `app/routes.py` - Admin functionality and main navigation
- **Puzzle Logic**: `app/puzzles.py` - Puzzle display, submission handling, and answer verification

### Key Features
- **User System**: Registration, login with Flask-Login, admin privileges
- **Issues**: Time-gated puzzle collections with PDF downloads
- **Puzzles**: Individual puzzles with hashed answers and submission tracking
- **Hints**: Time-released hints for puzzles
- **Admin Panel**: CRUD operations for users, puzzles, issues, and hints

### Blueprint Structure
- `auth` - Authentication routes (/register, /login, /logout)
- `main` - Main application routes (index redirect)
- `admin` - Admin functionality (/admin/*)
- `puzzle` - Puzzle and issue routes (/puzzles, /issues, /puzzle/<id>, /issue/<id>)

### Answer Verification
- Answers are normalized (lowercase, no punctuation/spaces) via `normalize_answer()` in `app/puzzles.py:11`
- Answer hashes are stored using Werkzeug's `generate_password_hash`
- Verification uses `check_password_hash` with normalized input

### Time Management
- All datetime objects use UTC timezone
- Issues have `available_date` that controls puzzle access
- Hints have `unlock_date` controlling visibility
- Date comparison utility in `app/utils.py`

### Configuration
- Development config in `app/__init__.py` (SECRET_KEY='dev', SQLite database)
- Instance configuration in `instance/config.py` (not tracked in git)
- Database URI: `sqlite:///puzzle_site.db`

### Static Files
- CSS: `app/static/style.css`
- PDFs: `app/static/pdfs/` (issue downloads)
- Templates: `app/templates/` with Jinja2 base template inheritance

### Dependencies
Flask ecosystem with Flask-Login, Flask-SQLAlchemy, Flask-WTF, WTForms for form handling and validation.