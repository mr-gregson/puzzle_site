# Production Deployment Guide

This guide will help you deploy your Puzzle Site to production safely and securely.

## 🚨 Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Copy `.env.example` to `.env` and configure all variables
- [ ] Generate a strong SECRET_KEY (64+ random characters)
- [ ] Set up production database (PostgreSQL recommended)
- [ ] Configure email settings with proper credentials
- [ ] Set `FLASK_ENV=production`

### 2. Security Review
- [ ] Verify SECRET_KEY is not hardcoded
- [ ] Confirm database credentials are secure
- [ ] Review email configuration for production use
- [ ] Ensure HTTPS is configured (reverse proxy/load balancer)

### 3. Infrastructure
- [ ] Database server is ready and accessible
- [ ] Email service is configured and tested
- [ ] Domain/subdomain is configured
- [ ] SSL certificate is installed
- [ ] Firewall rules are configured

## 🔧 Deployment Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
1. Copy and edit environment file:
```bash
cp .env.example .env
# Edit .env with your production values
```

2. Generate a secure secret key:
```python
import secrets
print(secrets.token_hex(32))
```

### Step 3: Set Up Database
```bash
# Run database migrations
python migrations.py

# Optional: backup existing SQLite database
python migrations.py --backup
```

### Step 4: Test Email Configuration
```bash
python test_email.py
```

### Step 5: Start Production Server
```bash
# Make start script executable (Linux/Mac)
chmod +x start_production.sh

# Start the application
./start_production.sh
```

Or manually with Gunicorn:
```bash
gunicorn --config gunicorn.conf.py wsgi:app
```

## 🔍 Health Checks

The application provides several health check endpoints:

- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system health
- `GET /readiness` - Kubernetes readiness probe
- `GET /liveness` - Kubernetes liveness probe

## 📝 Environment Variables

### Required Variables
- `SECRET_KEY` - Flask secret key (generate randomly)
- `DATABASE_URL` - Production database URL
- `FLASK_ENV` - Set to `production`

### Email Configuration
- `MAIL_SERVER` - SMTP server (default: smtp.gmail.com)
- `MAIL_PORT` - SMTP port (default: 587)
- `MAIL_USE_TLS` - Use TLS (default: true)
- `MAIL_USERNAME` - Email account username
- `MAIL_PASSWORD` - Email account password (use App Password for Gmail)
- `MAIL_DEFAULT_SENDER` - Default sender email
- `PUZZLE_SITE_ADMIN` - Admin email for notifications

### Optional Variables
- `PORT` - Server port (default: 8000)
- `GUNICORN_WORKERS` - Number of worker processes
- `LOG_LEVEL` - Logging level (default: INFO)

## 🗄️ Database Recommendations

### Production Database Options
1. **PostgreSQL** (Recommended)
   ```
   DATABASE_URL=postgresql://username:password@hostname:5432/database
   ```

2. **MySQL/MariaDB**
   ```
   DATABASE_URL=mysql://username:password@hostname:3306/database
   ```

### Migration from SQLite
1. Export your current data
2. Set up your production database
3. Run `python migrations.py` to create tables
4. Import your data to the new database

## 🔒 Security Considerations

### HTTPS Configuration
- Use a reverse proxy (nginx, Apache) or load balancer for HTTPS
- Configure proper SSL/TLS certificates
- Set up HTTP to HTTPS redirects

### Firewall Rules
- Only expose necessary ports (80, 443, SSH)
- Restrict database access to application server only
- Use VPN or bastion host for administrative access

### Monitoring
- Set up log aggregation and monitoring
- Configure alerts for application errors
- Monitor resource usage (CPU, memory, disk)

## 🚀 Deployment Platforms

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
```

### Platform-as-a-Service
The application is compatible with:
- Heroku
- Google Cloud Run
- AWS Elastic Beanstalk
- Azure App Service

## 🧪 Testing

### Pre-deployment Tests
1. Run email test: `python test_email.py`
2. Check health endpoints: `curl http://localhost:8000/health`
3. Verify database connectivity
4. Test user registration and login flows
5. Verify puzzle functionality

### Post-deployment Tests
1. Test all health check endpoints
2. Verify HTTPS is working
3. Test email functionality in production
4. Check application logs for errors
5. Verify all features work correctly

## 📊 Monitoring and Maintenance

### Log Files
- Application logs: `logs/puzzle_site.log`
- Gunicorn logs: stdout/stderr
- Web server logs: depends on your setup

### Regular Maintenance
- Monitor disk space and clean old logs
- Keep dependencies updated
- Regular database backups
- Monitor application performance
- Review security updates

## 🆘 Troubleshooting

### Common Issues
1. **Email not working**: Check MAIL_* environment variables and test with `python test_email.py`
2. **Database errors**: Verify DATABASE_URL and run `python migrations.py`
3. **Permission errors**: Check file permissions and user ownership
4. **Port already in use**: Change PORT environment variable or stop conflicting services

### Getting Help
- Check application logs in `logs/puzzle_site.log`
- Use health check endpoints to diagnose issues
- Review environment variable configuration
- Verify all required services are running

## 🔄 Updates and Rollbacks

### Updating the Application
1. Backup your database and environment files
2. Pull latest code changes
3. Update dependencies: `pip install -r requirements.txt`
4. Run any new migrations
5. Restart the application

### Rollback Procedure
1. Stop the application
2. Restore previous code version
3. Restore database backup if needed
4. Restart application
5. Verify functionality

---

🎉 **Congratulations!** Your Puzzle Site should now be running in production mode with proper security, monitoring, and error handling.