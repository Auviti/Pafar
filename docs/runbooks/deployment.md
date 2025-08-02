# Deployment Runbook

## Overview
This runbook covers deployment procedures for the Pafar Transport Management Platform.

## Prerequisites
- Access to production servers
- Docker and Docker Compose installed
- SSH keys configured
- Environment variables set

## Production Deployment

### Automated Deployment (Recommended)
1. **Trigger via GitHub Actions:**
   ```bash
   # Push to main branch triggers automatic deployment
   git push origin main
   
   # Or manually trigger deployment
   gh workflow run deploy-production.yml
   ```

2. **Monitor deployment:**
   - Check GitHub Actions workflow status
   - Monitor application logs
   - Verify health endpoints

### Manual Deployment (Emergency)
1. **Connect to production server:**
   ```bash
   ssh deploy@production-server
   cd /opt/pafar
   ```

2. **Create backup:**
   ```bash
   # Database backup
   ./scripts/postgres-backup.sh
   
   # Application backup
   docker-compose -f docker-compose.prod.yml exec backend tar -czf /tmp/app-backup.tar.gz /app
   ```

3. **Pull latest images:**
   ```bash
   docker login ghcr.io
   docker-compose -f docker-compose.prod.yml pull
   ```

4. **Deploy with zero downtime:**
   ```bash
   # Rolling update
   docker-compose -f docker-compose.prod.yml up -d --no-deps backend
   docker-compose -f docker-compose.prod.yml up -d --no-deps frontend
   
   # Run migrations
   docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

5. **Verify deployment:**
   ```bash
   # Check service health
   curl -f https://yourdomain.com/health
   
   # Check service status
   docker-compose -f docker-compose.prod.yml ps
   
   # Check logs
   docker-compose -f docker-compose.prod.yml logs --tail=50
   ```

## Rollback Procedures

### Quick Rollback
1. **Identify last known good version:**
   ```bash
   docker images | grep pafar
   ```

2. **Update docker-compose to use previous version:**
   ```bash
   # Edit docker-compose.prod.yml to use previous image tags
   vim docker-compose.prod.yml
   ```

3. **Deploy previous version:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Database Rollback
1. **Stop application:**
   ```bash
   docker-compose -f docker-compose.prod.yml stop backend celery-worker
   ```

2. **Restore database:**
   ```bash
   ./scripts/postgres-restore.sh backup_file.sql.gz
   ```

3. **Restart application:**
   ```bash
   docker-compose -f docker-compose.prod.yml start backend celery-worker
   ```

## Environment Management

### Environment Variables
```bash
# Production environment file location
/opt/pafar/.env

# Required variables:
DATABASE_URL=postgresql://user:pass@db:5432/pafar_db
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key
STRIPE_SECRET_KEY=sk_live_...
GOOGLE_MAPS_API_KEY=your-api-key
```

### SSL Certificate Management
```bash
# Certificate location
/opt/pafar/ssl/

# Renew certificates (if using Let's Encrypt)
certbot renew --nginx

# Update certificates in Docker
docker-compose -f docker-compose.prod.yml restart nginx
```

## Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   # Check logs
   docker-compose -f docker-compose.prod.yml logs service-name
   
   # Check resource usage
   docker stats
   
   # Check disk space
   df -h
   ```

2. **Database connection issues:**
   ```bash
   # Check database status
   docker-compose -f docker-compose.prod.yml exec db pg_isready
   
   # Check connections
   docker-compose -f docker-compose.prod.yml exec db psql -U $POSTGRES_USER -c "SELECT * FROM pg_stat_activity;"
   ```

3. **High memory usage:**
   ```bash
   # Check memory usage
   free -h
   docker stats --no-stream
   
   # Restart services if needed
   docker-compose -f docker-compose.prod.yml restart
   ```

## Monitoring and Alerts

### Health Checks
- Application: `https://yourdomain.com/health`
- Database: `docker-compose exec db pg_isready`
- Redis: `docker-compose exec redis redis-cli ping`

### Log Locations
- Application logs: `docker-compose logs`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`

### Grafana Dashboards
- System Overview: http://monitoring.yourdomain.com:3001
- Default credentials: admin / (check GRAFANA_PASSWORD)

## Emergency Contacts
- DevOps Team: devops@company.com
- On-call Engineer: +1-xxx-xxx-xxxx
- Slack Channel: #pafar-alerts