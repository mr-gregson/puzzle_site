# IT Deployment Guide - Puzzle Competition Site

## 🚀 Quick Start for IT Teams

This Flask web application is containerized and ready for production deployment. This guide provides everything your IT team needs to deploy and manage the Puzzle Site.

## 📋 System Requirements

### Infrastructure Requirements
- **Container Runtime**: Docker 20.10+ or containerd
- **Database**: PostgreSQL 13+ (recommended) or MySQL 8+
- **Memory**: 512MB minimum, 1GB recommended per container
- **Storage**: 10GB for application, additional for database
- **Network**: HTTP/HTTPS access, SMTP access for emails

### Security Requirements
- **HTTPS/TLS**: Required for production (handle via reverse proxy/load balancer)
- **Database**: Isolated network, no public access
- **Secrets Management**: Environment variables via secure secrets management
- **User Access**: Non-root container execution (already configured)

## 🔧 Container Configuration

### Pre-built Image
```bash
# Build the image
docker build -t puzzle-site:latest .

# Or use docker-compose for testing
docker-compose up -d
```

### Container Specifications
- **Base Image**: `python:3.11-slim`
- **Exposed Port**: `8000`
- **User**: `puzzleuser` (non-root)
- **Health Check**: `/health` endpoint
- **Volumes**: `/app/logs`, `/app/app/static/pdfs`

## 🔐 Environment Variables (REQUIRED)

### Critical Security Variables
```bash
SECRET_KEY=<64-char-random-string>           # REQUIRED: Generate securely
FLASK_ENV=production                         # REQUIRED: Must be 'production'
DATABASE_URL=postgresql://user:pass@host:5432/db  # REQUIRED: Production database
```

### Email Configuration (REQUIRED for user registration)
```bash
MAIL_SERVER=smtp.yourdomain.com              # SMTP server hostname
MAIL_PORT=587                                # SMTP port (587 for TLS)
MAIL_USE_TLS=true                           # Enable TLS encryption
MAIL_USERNAME=noreply@yourdomain.com        # SMTP authentication username
MAIL_PASSWORD=<smtp-password>               # SMTP authentication password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com  # Default sender address
PUZZLE_SITE_ADMIN=admin@yourdomain.com      # Admin notification email
```

### Optional Configuration
```bash
PORT=8000                                   # Application port (default: 8000)
GUNICORN_WORKERS=4                          # Worker processes (default: CPU count)
LOG_LEVEL=INFO                              # Logging level (DEBUG/INFO/WARNING/ERROR)
```

## 🗄️ Database Setup

### PostgreSQL (Recommended)
```sql
-- Create database and user
CREATE DATABASE puzzlesite;
CREATE USER puzzleuser WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE puzzlesite TO puzzleuser;
```

### Connection String Format
```bash
# PostgreSQL
DATABASE_URL=postgresql://puzzleuser:password@db-host:5432/puzzlesite

# MySQL (alternative)
DATABASE_URL=mysql://puzzleuser:password@db-host:3306/puzzlesite
```

### Database Initialization
The application automatically creates tables on first run. To create an admin user:

```bash
# Run database setup (creates tables + admin user)
docker exec -it <container-name> python migrations.py
```

## 🚀 Deployment Options

### Option 1: Docker Compose (Development/Testing)
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with production values

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Option 2: Container Orchestration (Production)
For production, use Kubernetes, Docker Swarm, or your preferred orchestration platform.

#### Sample Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: puzzle-site
spec:
  replicas: 2
  selector:
    matchLabels:
      app: puzzle-site
  template:
    metadata:
      labels:
        app: puzzle-site
    spec:
      containers:
      - name: puzzle-site
        image: puzzle-site:latest
        ports:
        - containerPort: 8000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: puzzle-secrets
              key: secret-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: puzzle-secrets
              key: database-url
        # ... other environment variables
        livenessProbe:
          httpGet:
            path: /liveness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 📊 Monitoring and Health Checks

### Health Check Endpoints
- `GET /health` - Basic application health
- `GET /health/detailed` - Detailed system status with database connectivity
- `GET /liveness` - Kubernetes liveness probe (application is running)
- `GET /readiness` - Kubernetes readiness probe (ready to accept traffic)

### Expected Responses
```bash
# Healthy response
curl http://localhost:8000/health
# {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}

# Detailed health check
curl http://localhost:8000/health/detailed
# {"status": "healthy", "database": "connected", "timestamp": "...", "version": "1.0"}
```

### Log Files
- **Application logs**: `/app/logs/puzzle_site.log`
- **Container logs**: `docker logs <container-name>`
- **Format**: JSON structured logging for production

## 🔒 Security Configuration

### Network Security
- Application runs on port 8000 internally
- Use reverse proxy (nginx/Apache) or load balancer for HTTPS termination
- Database should not be publicly accessible
- Implement network segmentation between tiers

### Secrets Management
- **Never** hardcode secrets in environment files
- Use your organization's secrets management system:
  - Kubernetes Secrets
  - Docker Secrets
  - HashiCorp Vault
  - Cloud provider secret managers

### Security Headers
The application automatically sets these security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (when HTTPS is used)

## 🧪 Testing and Validation

### Pre-deployment Testing
```bash
# 1. Test email configuration
docker exec -it <container> python test_email.py

# 2. Verify health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed

# 3. Test database connectivity
docker exec -it <container> python -c "from app import create_app; from app.models import db; app=create_app(); app.app_context().push(); print('DB:', db.engine.execute('SELECT 1').scalar())"
```

### Post-deployment Verification
1. ✅ Application starts without errors
2. ✅ Health checks return 200 status
3. ✅ Database connectivity confirmed
4. ✅ User registration flow works
5. ✅ Email delivery functional
6. ✅ HTTPS redirects working (if configured)
7. ✅ Admin panel accessible

## 🆘 Troubleshooting

### Common Issues

**Container won't start**
```bash
# Check logs
docker logs <container-name>

# Common causes:
# - Missing required environment variables
# - Database connectivity issues
# - Port already in use
```

**Database connection errors**
```bash
# Verify DATABASE_URL format
# Test database connectivity from container
docker exec -it <container> pg_isready -h <db-host> -p 5432 -U <username>
```

**Email not working**
```bash
# Test email configuration
docker exec -it <container> python test_email.py

# Check SMTP settings and credentials
```

### Support Information
- **Application logs**: `/app/logs/puzzle_site.log`
- **Health endpoint**: `/health/detailed` for diagnostic information
- **Database migrations**: Run `python migrations.py` if schema updates are needed

## 📈 Performance and Scaling

### Resource Requirements
- **CPU**: 0.5 cores minimum, 1 core recommended
- **Memory**: 512MB minimum, 1GB recommended
- **Storage**: 5GB application + database requirements
- **Network**: Standard HTTP/HTTPS + database connections

### Scaling Recommendations
- **Horizontal scaling**: Run multiple container replicas behind load balancer
- **Database scaling**: Use read replicas for heavy read workloads
- **File storage**: Use shared storage (NFS, object storage) for PDF files across replicas
- **Session storage**: Consider Redis for session storage in multi-replica deployments

---

## 📞 Handover Checklist

**Before deployment, ensure you have:**
- [ ] Generated secure SECRET_KEY (64+ characters)
- [ ] Configured production database with proper credentials
- [ ] Set up email SMTP configuration and tested delivery
- [ ] Configured HTTPS termination at load balancer/reverse proxy
- [ ] Set up monitoring and log aggregation
- [ ] Planned backup strategy for database and uploaded files
- [ ] Reviewed and configured all required environment variables

**Contact Information:**
- **Developer**: [Your contact information]
- **Documentation**: See `DEPLOYMENT.md` for additional technical details
- **Source Code**: [Repository URL if applicable]

🎉 **Ready for Production!** This application is designed with IT operations in mind and follows containerization best practices.