# Environment Variables Reference

This document provides a complete reference for all environment variables used by the Puzzle Site application.

## 🔐 Required Variables

### Application Core
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_ENV` | **Yes** | - | Must be `production` for production deployment |
| `SECRET_KEY` | **Yes** | - | Flask secret key (64+ random characters). Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |

### Database Configuration
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | **Yes** | - | Full database connection URL. Format: `postgresql://user:pass@host:port/db` or `mysql://user:pass@host:port/db` |

### Email Configuration (Required for user registration)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAIL_SERVER` | **Yes** | - | smtp.sendgrid.net |
| `MAIL_PORT` | **Yes** | - | `587` SMTP server port (usually `587` for TLS, `465` for SSL, `25` for plain) |
| `MAIL_USE_TLS` | **Yes** | - | true |
| `MAIL_USERNAME` | **Yes** | - | SMTP authentication username |
| `MAIL_PASSWORD` | **Yes** | - | SMTP authentication password (use App Password for Gmail) |
| `MAIL_DEFAULT_SENDER` | **Yes** | - | Default sender email address |
| `PUZZLE_SITE_ADMIN` | **Yes** | - | froot.magazine@utschools.ca |

## ⚙️ Optional Variables

### Server Configuration
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | `8000` | Port number for the application server |
| `GUNICORN_WORKERS` | No | CPU count | Number of Gunicorn worker processes |

### Logging and Monitoring
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

### Security (Optional but Recommended)
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAIL_USE_SSL` | No | `false` | Use SSL instead of TLS for email (`true` or `false`) |
| `SESSION_COOKIE_SECURE` | No | Auto-detected | Force HTTPS for session cookies (`true` or `false`) |

## 🛡️ Security Best Practices

### Secret Key Generation
```bash
# Generate a secure SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

### Database URL Examples
```bash
# PostgreSQL (recommended)
DATABASE_URL=postgresql://puzzleuser:secure_password@db.company.com:5432/puzzlesite

# PostgreSQL with SSL
DATABASE_URL=postgresql://puzzleuser:secure_password@db.company.com:5432/puzzlesite?sslmode=require

# MySQL/MariaDB
DATABASE_URL=mysql://puzzleuser:secure_password@db.company.com:3306/puzzlesite

# SQLite (development only)
DATABASE_URL=sqlite:///puzzle_site.db
```

### Email Configuration Examples

#### Gmail with App Password
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-account@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

#### Corporate Exchange Server
```bash
MAIL_SERVER=mail.company.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=service-account@company.com
MAIL_PASSWORD=service-account-password
MAIL_DEFAULT_SENDER=puzzle-noreply@company.com
```

#### SendGrid
```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

## 📝 Environment File Template

Create a `.env` file based on this template:

```bash
# Application Configuration
FLASK_ENV=production
SECRET_KEY=your-64-character-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://username:password@hostname:5432/database_name

# Email Configuration
MAIL_SERVER=smtp.yourdomain.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=your-smtp-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
PUZZLE_SITE_ADMIN=admin@yourdomain.com

# Optional Configuration
PORT=8000
GUNICORN_WORKERS=4
LOG_LEVEL=INFO
```

## 🔍 Validation

The application validates required environment variables on startup. If any required variables are missing, the application will:

1. Log detailed error messages
2. Exit with a non-zero status code
3. Display helpful guidance for missing variables

### Testing Configuration
```bash
# Test all environment variables are properly set
python wsgi.py --test-config

# Test email configuration specifically
python test_email.py
```

## 🐳 Docker Environment Variables

### Docker Compose
```yaml
environment:
  - FLASK_ENV=production
  - SECRET_KEY=${SECRET_KEY}
  - DATABASE_URL=${DATABASE_URL}
  - MAIL_SERVER=${MAIL_SERVER}
  # ... other variables
```

### Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: puzzle-site-secrets
type: Opaque
data:
  secret-key: base64-encoded-secret-key
  database-url: base64-encoded-database-url
  mail-password: base64-encoded-mail-password
```

## ⚠️ Security Warnings

### Do NOT include in source control:
- `.env` files with real values
- Any files containing passwords or secret keys
- Database connection strings with credentials

### Do NOT use in production:
- `SECRET_KEY='dev'` or any hardcoded values
- `FLASK_ENV=development`
- Default or example passwords
- Unencrypted SMTP connections in production

### Always use:
- Randomly generated SECRET_KEY values
- Secure password policies for database and email accounts
- TLS/SSL for all network connections
- Your organization's secrets management system

## 🔄 Environment-Specific Configurations

### Development
```bash
FLASK_ENV=development  # Enables debug mode, auto-reload
DATABASE_URL=sqlite:///puzzle_site.db  # Local SQLite database
LOG_LEVEL=DEBUG  # Verbose logging
```

### Testing
```bash
FLASK_ENV=testing  # Disables CSRF, enables test mode
DATABASE_URL=sqlite:///:memory:  # In-memory database
LOG_LEVEL=WARNING  # Reduced logging
```

### Production
```bash
FLASK_ENV=production  # Optimized for performance
DATABASE_URL=postgresql://...  # Production database
LOG_LEVEL=INFO  # Standard logging
SESSION_COOKIE_SECURE=true  # HTTPS required for cookies
```