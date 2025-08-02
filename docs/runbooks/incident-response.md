# Incident Response Runbook

## Overview
This runbook provides procedures for responding to production incidents in the Pafar platform.

## Incident Classification

### Severity Levels

**P0 - Critical (Complete Outage)**
- Service completely unavailable
- Data loss or corruption
- Security breach
- Response time: Immediate (< 15 minutes)

**P1 - High (Major Functionality Impacted)**
- Core features unavailable (booking, payment)
- Significant performance degradation
- Response time: < 1 hour

**P2 - Medium (Minor Functionality Impacted)**
- Non-core features affected
- Minor performance issues
- Response time: < 4 hours

**P3 - Low (Minimal Impact)**
- Cosmetic issues
- Documentation problems
- Response time: Next business day

## Incident Response Process

### 1. Detection and Alert
- **Automated alerts** via Prometheus/Grafana
- **User reports** via support channels
- **Monitoring dashboards** showing anomalies

### 2. Initial Response (0-15 minutes)

1. **Acknowledge the incident:**
   ```bash
   # Acknowledge in monitoring system
   # Update incident tracking system
   ```

2. **Assess severity:**
   - Check service availability
   - Review error rates and metrics
   - Determine user impact

3. **Assemble response team:**
   - Incident Commander
   - Technical Lead
   - Communications Lead

4. **Create incident channel:**
   ```
   Slack: #incident-YYYY-MM-DD-HHMM
   ```

### 3. Investigation and Diagnosis (15-60 minutes)

1. **Gather information:**
   ```bash
   # Check service status
   docker-compose -f docker-compose.prod.yml ps
   
   # Review recent changes
   git log --oneline --since="2 hours ago"
   
   # Check system resources
   docker stats --no-stream
   free -h
   df -h
   ```

2. **Review logs:**
   ```bash
   # Application logs
   docker-compose -f docker-compose.prod.yml logs --tail=100 backend
   
   # System logs
   journalctl -u docker --since "1 hour ago"
   
   # Nginx logs
   tail -100 /var/log/nginx/error.log
   ```

3. **Check monitoring dashboards:**
   - System Overview Dashboard
   - Application Performance Dashboard
   - Database Dashboard

### 4. Mitigation and Resolution

#### Quick Fixes

1. **Service restart:**
   ```bash
   # Restart specific service
   docker-compose -f docker-compose.prod.yml restart backend
   
   # Full system restart (last resort)
   docker-compose -f docker-compose.prod.yml restart
   ```

2. **Scale services:**
   ```bash
   # Scale backend service
   docker-compose -f docker-compose.prod.yml up -d --scale backend=3
   ```

3. **Rollback deployment:**
   ```bash
   # Quick rollback to previous version
   git checkout HEAD~1
   docker-compose -f docker-compose.prod.yml up -d
   ```

#### Database Issues

1. **Connection pool exhaustion:**
   ```bash
   # Check active connections
   docker-compose exec db psql -U $POSTGRES_USER -c "SELECT count(*) FROM pg_stat_activity;"
   
   # Kill long-running queries
   docker-compose exec db psql -U $POSTGRES_USER -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';"
   ```

2. **Lock contention:**
   ```bash
   # Check for locks
   docker-compose exec db psql -U $POSTGRES_USER -c "SELECT * FROM pg_locks WHERE NOT granted;"
   
   # Kill blocking queries
   docker-compose exec db psql -U $POSTGRES_USER -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid IN (SELECT blocking_pid FROM pg_blocking_pids());"
   ```

3. **Disk space issues:**
   ```bash
   # Check disk usage
   df -h
   
   # Clean up old logs
   docker system prune -f
   
   # Clean up old backups
   find /var/backups/postgresql -name "*.sql.gz" -mtime +7 -delete
   ```

#### Performance Issues

1. **High CPU usage:**
   ```bash
   # Identify CPU-intensive processes
   docker stats --no-stream
   
   # Check for runaway queries
   docker-compose exec db psql -U $POSTGRES_USER -c "SELECT pid, query, query_start FROM pg_stat_activity WHERE state = 'active' ORDER BY query_start;"
   ```

2. **Memory issues:**
   ```bash
   # Check memory usage
   free -h
   docker stats --format "table {{.Container}}\t{{.MemUsage}}"
   
   # Restart memory-intensive services
   docker-compose -f docker-compose.prod.yml restart backend celery-worker
   ```

3. **Network issues:**
   ```bash
   # Test external connectivity
   curl -f https://api.stripe.com/v1/charges
   curl -f https://maps.googleapis.com/maps/api/geocode/json
   
   # Test internal connectivity
   docker-compose exec backend curl -f http://db:5432
   docker-compose exec backend curl -f http://redis:6379
   ```

### 5. Communication

#### Internal Communication
- **Incident channel updates** every 15-30 minutes
- **Status page updates** for customer-facing issues
- **Stakeholder notifications** for P0/P1 incidents

#### External Communication
```
Subject: [RESOLVED] Service Disruption - Booking System

We experienced a service disruption affecting our booking system from 
14:30 to 15:15 UTC today. The issue has been resolved and all services 
are now operating normally.

Root cause: Database connection pool exhaustion
Resolution: Increased connection pool size and restarted services

We apologize for any inconvenience caused.
```

### 6. Post-Incident Activities

1. **Document timeline:**
   - When incident started
   - Detection time
   - Response actions taken
   - Resolution time

2. **Conduct post-mortem:**
   - Root cause analysis
   - Contributing factors
   - Lessons learned
   - Action items

3. **Update runbooks:**
   - Add new troubleshooting steps
   - Update contact information
   - Improve monitoring/alerting

## Common Incident Scenarios

### Scenario 1: Payment System Down

**Symptoms:**
- Payment failures
- Stripe webhook errors
- User complaints about failed transactions

**Investigation:**
```bash
# Check payment service logs
docker-compose logs backend | grep -i payment

# Test Stripe connectivity
curl -f https://api.stripe.com/v1/charges \
  -H "Authorization: Bearer $STRIPE_SECRET_KEY"

# Check webhook endpoint
curl -f https://yourdomain.com/api/webhooks/stripe
```

**Resolution:**
1. Verify Stripe API keys
2. Check webhook configuration
3. Restart payment service
4. Process failed payments manually if needed

### Scenario 2: Database Performance Degradation

**Symptoms:**
- Slow API responses
- High database CPU usage
- Connection timeouts

**Investigation:**
```bash
# Check slow queries
docker-compose exec db psql -U $POSTGRES_USER -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check active connections
docker-compose exec db psql -U $POSTGRES_USER -c "SELECT count(*) FROM pg_stat_activity;"

# Check locks
docker-compose exec db psql -U $POSTGRES_USER -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

**Resolution:**
1. Kill long-running queries
2. Add missing indexes
3. Increase connection pool size
4. Scale database if needed

### Scenario 3: High Memory Usage

**Symptoms:**
- OOM kills
- Slow response times
- Container restarts

**Investigation:**
```bash
# Check memory usage
free -h
docker stats --no-stream

# Check for memory leaks
docker-compose exec backend python -c "import psutil; print(psutil.virtual_memory())"
```

**Resolution:**
1. Restart affected services
2. Increase memory limits
3. Investigate memory leaks
4. Scale horizontally

## Emergency Contacts

### On-Call Rotation
- **Primary**: +1-xxx-xxx-xxxx
- **Secondary**: +1-xxx-xxx-xxxx
- **Escalation**: +1-xxx-xxx-xxxx

### Key Personnel
- **CTO**: cto@company.com
- **DevOps Lead**: devops-lead@company.com
- **Product Manager**: pm@company.com

### External Vendors
- **Hosting Provider**: support@hosting.com
- **Stripe Support**: https://support.stripe.com
- **Google Cloud Support**: https://cloud.google.com/support

## Tools and Resources

### Monitoring
- **Grafana**: http://monitoring.yourdomain.com:3001
- **Kibana**: http://monitoring.yourdomain.com:5601
- **Prometheus**: http://monitoring.yourdomain.com:9090

### Communication
- **Slack**: #pafar-incidents
- **Status Page**: https://status.yourdomain.com
- **Incident Tracking**: https://incidents.yourdomain.com

### Documentation
- **Architecture Docs**: /docs/architecture/
- **API Docs**: https://api.yourdomain.com/docs
- **Runbooks**: /docs/runbooks/

## Incident Response Checklist

### During Incident
- [ ] Incident acknowledged within 15 minutes
- [ ] Severity assessed and classified
- [ ] Incident channel created
- [ ] Response team assembled
- [ ] Initial investigation completed
- [ ] Mitigation actions taken
- [ ] Status page updated (if customer-facing)
- [ ] Stakeholders notified
- [ ] Resolution implemented
- [ ] Service recovery verified

### Post-Incident
- [ ] Incident timeline documented
- [ ] Post-mortem scheduled
- [ ] Root cause analysis completed
- [ ] Action items identified and assigned
- [ ] Runbooks updated
- [ ] Monitoring/alerting improved
- [ ] Customer communication sent (if applicable)
- [ ] Lessons learned shared with team