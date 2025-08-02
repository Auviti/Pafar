# Pafar Production Deployment Guide

## Overview

This guide covers the complete production deployment setup for the Pafar Transport Management Platform, including Docker containerization, monitoring, logging, and automated deployment pipelines.

## Architecture

The production deployment consists of:

- **Application Services**: Backend API, Frontend, Celery workers
- **Data Services**: PostgreSQL, Redis
- **Infrastructure**: Nginx load balancer with SSL termination
- **Monitoring**: Prometheus, Grafana, Node Exporter
- **Logging**: Elasticsearch, Logstash, Kibana (ELK Stack)
- **Backup**: Automated PostgreSQL backups with retention

## Prerequisites

### Server Requirements

**Minimum Production Server Specs:**
- 4 CPU cores
- 8GB RAM
- 100GB SSD storage
- Ubuntu 20.04 LTS or later

**Recommended Production Server Specs:**
- 8 CPU cores
- 16GB RAM
- 200GB SSD storage
- Load balancer for high availability

### Software Requirements

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt update
sudo apt install -y curl wget git nginx certbot
```

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/pafar.git
cd pafar
```

### 2. Configure Environment Variables

```bash
# Copy environment template
cp .env.production.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**

```bash
# Database
POSTGRES_DB=pafar_production
POSTGRES_USER=pafar_user
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://pafar_user:password@db:5432/pafar_production

# Redis
REDIS_URL=redis://:password@redis:6379/0
REDIS_PASSWORD=your_redis_password

# Application
SECRET_KEY=your_very_long_secret_key
ENVIRONMENT=production

# External APIs
STRIPE_SECRET_KEY=sk_live_your_stripe_key
GOOGLE_MAPS_API_KEY=your_google_maps_key

# Domain
DOMAIN_NAME=yourdomain.com
API_URL=https://yourdomain.com/api
WS_URL=wss://yourdomain.com/ws
```

### 3. SSL Certificate Setup

#### Option A: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
sudo chown -R $USER:$USER ssl/
```

#### Option B: Custom Certificate

```bash
# Create ssl directory
mkdir -p ssl

# Copy your certificate files
cp your-certificate.pem ssl/cert.pem
cp your-private-key.pem ssl/key.pem
```

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

#### GitHub Actions Setup

1. **Configure Repository Secrets:**

```bash
# Server access
DEPLOY_SSH_KEY=your_private_ssh_key
SERVER_HOST=your.server.ip
SERVER_USER=deploy

# Environment variables
DATABASE_URL=postgresql://user:pass@db:5432/pafar_db
REDIS_URL=redis://:pass@redis:6379/0
SECRET_KEY=your_secret_key
STRIPE_SECRET_KEY=sk_live_your_key
GOOGLE_MAPS_API_KEY=your_api_key
GRAFANA_PASSWORD=your_grafana_password
```

2. **Deploy via Git Push:**

```bash
# Deploy to production
git push origin main

# Deploy to staging
git push origin develop
```

3. **Manual Trigger:**

```bash
# Using GitHub CLI
gh workflow run deploy-production.yml

# Or via GitHub web interface
```

### Method 2: Manual Deployment

#### Production Deployment

```bash
# Run deployment script
./scripts/deploy.sh production

# Or step by step
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

#### Staging Deployment

```bash
# Deploy to staging
./scripts/deploy.sh staging

# Or using staging compose file
docker-compose -f docker-compose.staging.yml up -d
```

## Monitoring Setup

### Grafana Dashboard Access

```
URL: http://your-server:3001
Username: admin
Password: (from GRAFANA_PASSWORD env var)
```

### Prometheus Metrics

```
URL: http://your-server:9090
```

### Log Analysis (Kibana)

```
URL: http://your-server:5601
```

### Key Metrics to Monitor

- **Application Health**: Service uptime, response times
- **Business Metrics**: Bookings per hour, payment success rate
- **System Resources**: CPU, memory, disk usage
- **Database Performance**: Connection count, query performance
- **Error Rates**: 4xx/5xx responses, application errors

## Backup and Recovery

### Automated Backups

```bash
# Setup automated backups
sudo ./scripts/setup-backup-cron.sh

# Manual backup
./scripts/postgres-backup.sh

# List backups
ls -la /var/backups/postgresql/
```

### Database Recovery

```bash
# List available backups
./scripts/postgres-restore.sh --list

# Restore from specific backup
./scripts/postgres-restore.sh pafar_backup_20231201_120000.sql.gz

# Restore latest backup
./scripts/postgres-restore.sh latest
```

## Security Considerations

### SSL/TLS Configuration

- TLS 1.2+ only
- Strong cipher suites
- HSTS headers
- Certificate pinning

### Network Security

```bash
# Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3001/tcp  # Grafana (restrict to admin IPs)
```

### Application Security

- Environment variables for secrets
- JWT token expiration
- Rate limiting
- Input validation
- SQL injection protection

## Performance Optimization

### Database Optimization

```sql
-- Create indexes for frequently queried columns
CREATE INDEX CONCURRENTLY idx_bookings_user_id ON bookings(user_id);
CREATE INDEX CONCURRENTLY idx_bookings_trip_id ON bookings(trip_id);
CREATE INDEX CONCURRENTLY idx_trips_departure_time ON trips(departure_time);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM bookings WHERE user_id = 'uuid';
```

### Application Scaling

```bash
# Scale backend services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=2
```

### Caching Strategy

- Redis for session storage
- Application-level caching for frequent queries
- CDN for static assets
- Database query result caching

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   docker-compose -f docker-compose.prod.yml logs service-name
   
   # Check resource usage
   docker stats
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connectivity
   docker-compose -f docker-compose.prod.yml exec db pg_isready
   
   # Check connection count
   docker-compose -f docker-compose.prod.yml exec db psql -U $POSTGRES_USER -c "SELECT count(*) FROM pg_stat_activity;"
   ```

3. **SSL Certificate Issues**
   ```bash
   # Check certificate expiration
   openssl x509 -in ssl/cert.pem -text -noout | grep "Not After"
   
   # Renew Let's Encrypt certificate
   sudo certbot renew
   ```

### Health Checks

```bash
# Run comprehensive verification
./scripts/verify-deployment.sh production

# Check individual services
curl -f https://yourdomain.com/health
curl -f https://yourdomain.com/api/docs
```

## Maintenance

### Regular Tasks

1. **Weekly**
   - Review monitoring dashboards
   - Check backup integrity
   - Update dependencies

2. **Monthly**
   - Security updates
   - Performance review
   - Capacity planning

3. **Quarterly**
   - Disaster recovery testing
   - Security audit
   - Architecture review

### Update Procedures

```bash
# Update application
git pull origin main
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Update system packages
sudo apt update && sudo apt upgrade

# Update Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

## Disaster Recovery

### Backup Strategy

- **Database**: Daily automated backups with 30-day retention
- **Application**: Docker images stored in registry
- **Configuration**: Version controlled in Git
- **SSL Certificates**: Automated renewal with Let's Encrypt

### Recovery Procedures

1. **Complete System Failure**
   ```bash
   # Provision new server
   # Install Docker and dependencies
   # Clone repository
   # Restore database from backup
   # Deploy application
   ```

2. **Database Corruption**
   ```bash
   # Stop application services
   # Restore database from latest backup
   # Verify data integrity
   # Restart services
   ```

## Support and Contacts

### Emergency Contacts

- **DevOps Team**: devops@company.com
- **On-call Engineer**: +1-xxx-xxx-xxxx
- **Incident Channel**: #pafar-incidents

### Documentation

- **API Documentation**: https://api.yourdomain.com/docs
- **Architecture Docs**: /docs/architecture/
- **Runbooks**: /docs/runbooks/

### External Services

- **Hosting Provider**: support@hosting.com
- **Stripe Support**: https://support.stripe.com
- **Google Cloud Support**: https://cloud.google.com/support