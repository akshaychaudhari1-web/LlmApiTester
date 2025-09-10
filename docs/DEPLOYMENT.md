# Deployment Guide

## Overview

This guide covers deploying the Automotive Chat Assistant from development to production environments, including Replit deployment, traditional hosting, and cloud platforms.

## Quick Start - Replit Deployment

### Prerequisites
- Replit account
- OpenRouter API key
- Basic understanding of environment variables

### Environment Setup
```bash
# In Replit's Secrets tab, add:
SESSION_SECRET=your-cryptographically-strong-secret-here
DATABASE_URL=postgresql://provided-by-replit
OPENROUTER_API_KEY=your-openrouter-key-here  # Optional
```

### Automated Deployment
```bash
# Replit automatically detects the project type and runs:
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Verification
1. **Check Workflow Status**: Ensure "Start application" workflow is running
2. **Test Database**: Verify PostgreSQL connection in console
3. **API Testing**: Configure OpenRouter key in Settings and test
4. **Conversation Memory**: Test multi-turn automotive conversations

## Production Deployment

### Environment Requirements

#### System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3-pip postgresql-client nginx

# CentOS/RHEL
sudo yum install python3.11 python3-pip postgresql nginx
```

#### Python Dependencies
```bash
pip install -r requirements.txt
```

**requirements.txt:**
```txt
flask==2.3.3
flask-sqlalchemy==3.0.5
gunicorn==21.2.0
psycopg2-binary==2.9.7
requests==2.31.0
werkzeug==2.3.7
```

### Database Setup

#### PostgreSQL Configuration
```sql
-- Create database and user
CREATE DATABASE automotive_chat;
CREATE USER chat_app WITH ENCRYPTED PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE automotive_chat TO chat_app;

-- Connect to the database
\c automotive_chat;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO chat_app;
```

#### Database URL Configuration
```bash
# Production database URL format
DATABASE_URL=postgresql://chat_app:secure_password_here@localhost:5432/automotive_chat
```

### Application Configuration

#### Production Environment Variables
```bash
# /etc/environment or in deployment config
export FLASK_ENV=production
export SESSION_SECRET=cryptographically-secure-secret-key-min-32-chars
export DATABASE_URL=postgresql://user:pass@host:port/dbname
export OPENROUTER_API_KEY=your-openrouter-api-key
export WORKERS=4
export BIND=0.0.0.0:8000
```

#### Security Configuration
```python
# Production configuration (add to app.py)
if app.env == 'production':
    app.config.update(
        SESSION_COOKIE_SECURE=True,      # HTTPS only
        SESSION_COOKIE_HTTPONLY=True,    # Prevent XSS
        SESSION_COOKIE_SAMESITE='Lax',   # CSRF protection
        PERMANENT_SESSION_LIFETIME=3600, # 1 hour sessions
    )
```

### Gunicorn Configuration

#### gunicorn.conf.py
```python
# Gunicorn configuration file
import os

# Server socket
bind = os.getenv('BIND', '0.0.0.0:8000')
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', 4))
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests (prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'automotive_chat'

# Server mechanics
preload_app = True
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = 'www-data'
group = 'www-data'
tmp_upload_dir = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

#### Start Script
```bash
#!/bin/bash
# start.sh

# Activate virtual environment if using one
source venv/bin/activate

# Start Gunicorn with configuration
exec gunicorn --config gunicorn.conf.py main:app
```

### Nginx Configuration

#### Reverse Proxy Setup
```nginx
# /etc/nginx/sites-available/automotive-chat
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Static files
    location /static/ {
        alias /path/to/your/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Application proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffers
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 16 8k;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

#### Enable Site
```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/automotive-chat /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

### Systemd Service

#### Service Configuration
```ini
# /etc/systemd/system/automotive-chat.service
[Unit]
Description=Automotive Chat Assistant
After=network.target postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/app/venv/bin
ExecStart=/path/to/your/app/venv/bin/gunicorn --config gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

# Environment variables
EnvironmentFile=/etc/automotive-chat/environment

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/tmp /var/log/automotive-chat

[Install]
WantedBy=multi-user.target
```

#### Environment File
```bash
# /etc/automotive-chat/environment
FLASK_ENV=production
SESSION_SECRET=your-secure-secret-here
DATABASE_URL=postgresql://user:pass@localhost/automotive_chat
OPENROUTER_API_KEY=your-openrouter-key
WORKERS=4
BIND=0.0.0.0:8000
```

#### Service Management
```bash
# Enable and start service
sudo systemctl enable automotive-chat.service
sudo systemctl start automotive-chat.service

# Check status
sudo systemctl status automotive-chat.service

# View logs
sudo journalctl -u automotive-chat.service -f
```

## Cloud Platform Deployment

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["gunicorn", "--config", "gunicorn.conf.py", "main:app"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/automotive_chat
      - SESSION_SECRET=${SESSION_SECRET}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=automotive_chat
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  redis:
    image: redis:alpine
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

### AWS Deployment

#### Elastic Beanstalk
```yaml
# .ebextensions/01_packages.config
packages:
  yum:
    postgresql-devel: []

# .ebextensions/02_environment.config
option_settings:
  aws:elasticbeanstalk:application:environment:
    FLASK_ENV: production
    SESSION_SECRET: your-secret-here
    DATABASE_URL: postgresql://user:pass@rds-endpoint/dbname
```

#### ECS Task Definition
```json
{
  "family": "automotive-chat",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "automotive-chat",
      "image": "your-account.dkr.ecr.region.amazonaws.com/automotive-chat:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "SESSION_SECRET",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:session-secret"
        },
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:database-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/automotive-chat",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

#### App Engine Deployment
```yaml
# app.yaml
runtime: python311

env_variables:
  FLASK_ENV: production
  SESSION_SECRET: your-secret-here
  DATABASE_URL: postgresql://user:pass@private-ip/dbname

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6

vpc_access_connector:
  name: projects/PROJECT_ID/locations/REGION/connectors/CONNECTOR_NAME
```

#### Cloud Run Deployment
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/automotive-chat
gcloud run deploy automotive-chat \
  --image gcr.io/PROJECT_ID/automotive-chat \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FLASK_ENV=production \
  --set-secrets SESSION_SECRET=session-secret:latest \
  --set-secrets DATABASE_URL=database-url:latest
```

## Production Optimizations

### Session Storage Scaling

#### Redis Implementation
```python
# Enhanced session storage for production
import redis
from flask_session import Session

class ProductionSessionConfig:
    """Production-ready session configuration"""
    
    def __init__(self, app):
        # Redis connection
        self.redis_client = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379'),
            decode_responses=True
        )
        
        # Flask-Session configuration
        app.config.update(
            SESSION_TYPE='redis',
            SESSION_REDIS=self.redis_client,
            SESSION_PERMANENT=True,
            SESSION_USE_SIGNER=True,
            SESSION_KEY_PREFIX='auto_chat:',
            PERMANENT_SESSION_LIFETIME=3600  # 1 hour
        )
        
        Session(app)
    
    def get_session_data(self, session_id):
        """Get session data with automatic TTL refresh"""
        key = f"secure_session:{session_id}"
        data = self.redis_client.hgetall(key)
        
        if data:
            # Refresh TTL on access
            self.redis_client.expire(key, 3600)
            return {
                'api_key': data.get('api_key', ''),
                'model': data.get('model', 'deepseek/deepseek-chat-v3-0324:free'),
                'chat_history': json.loads(data.get('chat_history', '[]'))
            }
        return self.create_new_session(session_id)
    
    def update_session_data(self, session_id, data):
        """Update session data with TTL"""
        key = f"secure_session:{session_id}"
        self.redis_client.hset(key, mapping={
            'api_key': data['api_key'],
            'model': data['model'],
            'chat_history': json.dumps(data['chat_history'])
        })
        self.redis_client.expire(key, 3600)
```

### Performance Monitoring

#### Application Metrics
```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics collection
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
CHAT_MESSAGES = Counter('chat_messages_total', 'Total chat messages processed')
API_CALLS = Counter('openrouter_api_calls_total', 'Total OpenRouter API calls', ['status'])

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    request_latency = time.time() - request.start_time
    REQUEST_LATENCY.observe(request_latency)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint).inc()
    return response

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### Load Balancing

#### Multiple Workers
```bash
# Production gunicorn configuration
gunicorn \
  --workers 4 \
  --worker-class sync \
  --worker-connections 1000 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --preload \
  --bind 0.0.0.0:8000 \
  main:app
```

#### Health Checks
```python
@app.route('/health')
def health_check():
    """Comprehensive health check for load balancers"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        # Test Redis connection (if using)
        if hasattr(app, 'redis_client'):
            app.redis_client.ping()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': app.config.get('VERSION', 'unknown')
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503
```

## Monitoring & Logging

### Structured Logging
```python
import structlog

# Configure structured logging for production
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Usage in application
logger = structlog.get_logger()

@app.route('/chat', methods=['POST'])
def chat():
    logger.info(
        "Chat request received",
        session_id=session_id,
        message_length=len(message),
        model=model
    )
```

### Error Tracking
```python
# Integration with error tracking services
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[
        FlaskIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,
    environment=os.getenv('FLASK_ENV', 'development')
)
```

## Backup & Recovery

### Database Backups
```bash
#!/bin/bash
# backup.sh - Automated PostgreSQL backup

BACKUP_DIR="/backups/automotive-chat"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="automotive_chat"

# Create backup
pg_dump $DB_NAME | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

# Keep only last 30 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to cloud storage (optional)
aws s3 cp "$BACKUP_DIR/backup_$DATE.sql.gz" s3://your-backup-bucket/
```

### Session Data Backup
```python
# Redis backup for session data
def backup_session_data():
    """Export active sessions for backup"""
    backup_data = {}
    
    for key in redis_client.scan_iter(match="secure_session:*"):
        session_data = redis_client.hgetall(key)
        backup_data[key] = session_data
    
    # Save to file or cloud storage
    with open(f"session_backup_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
        json.dump(backup_data, f)
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```python
# Debug database connectivity
@app.route('/debug/db')
def debug_db():
    try:
        result = db.session.execute('SELECT version()')
        return jsonify({'db_version': result.fetchone()[0]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### Memory Issues
```bash
# Monitor memory usage
htop
# or
ps aux | grep gunicorn

# Check for memory leaks
valgrind --tool=memcheck python main.py
```

#### Session Issues
```python
# Debug session problems
@app.route('/debug/session')
def debug_session():
    return jsonify({
        'session_id': session.get('secure_session_id'),
        'session_keys': list(session.keys()),
        'secure_sessions_count': len(secure_sessions)
    })
```

### Performance Issues
```bash
# Profile application performance
python -m cProfile -o profile.stats main.py

# Analyze profile
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

### Log Analysis
```bash
# Monitor application logs
tail -f /var/log/automotive-chat/app.log

# Search for errors
grep -i error /var/log/automotive-chat/app.log

# Monitor access patterns
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr
```

## Maintenance

### Regular Tasks
```bash
# Daily maintenance script
#!/bin/bash

# Rotate logs
logrotate /etc/logrotate.d/automotive-chat

# Clean up old sessions (if using file-based storage)
find /tmp -name "flask_session_*" -mtime +1 -delete

# Update SSL certificates (if using Let's Encrypt)
certbot renew --quiet

# Restart application if needed
systemctl reload automotive-chat
```

### Updates & Deployments
```bash
# Zero-downtime deployment with Gunicorn
kill -USR2 $MASTERPID  # Reload workers gracefully

# Database migrations (when needed)
flask db upgrade

# Static file updates
nginx -s reload
```

This deployment guide provides comprehensive coverage for taking the automotive chat assistant from development to production across various platforms and environments.