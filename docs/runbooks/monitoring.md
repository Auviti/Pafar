# Monitoring and Alerting Runbook

## Overview
This runbook covers monitoring, alerting, and troubleshooting procedures for the Pafar platform.

## Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **Elasticsearch**: Log aggregation
- **Kibana**: Log analysis
- **Node Exporter**: System metrics

## Key Metrics to Monitor

### Application Metrics
- **Request Rate**: `rate(http_requests_total[5m])`
- **Response Time**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **Error Rate**: `rate(http_requests_total{status=~"5.."}[5m])`
- **Active Users**: `active_sessions_total`

### System Metrics
- **CPU Usage**: `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- **Memory Usage**: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
- **Disk Usage**: `100 - ((node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes)`
- **Network I/O**: `rate(node_network_receive_bytes_total[5m])`

### Database Metrics
- **Connection Count**: `pg_stat_database_numbackends`
- **Query Performance**: `pg_stat_statements_mean_time`
- **Lock Waits**: `pg_locks_count`
- **Replication Lag**: `pg_replication_lag_seconds`

## Grafana Dashboards

### System Overview Dashboard
- URL: `http://monitoring.yourdomain.com:3001/d/system-overview`
- Panels:
  - Service health status
  - Request rate and response times
  - Error rates
  - Resource utilization

### Database Dashboard
- URL: `http://monitoring.yourdomain.com:3001/d/database`
- Panels:
  - Connection pools
  - Query performance
  - Lock contention
  - Backup status

### Application Dashboard
- URL: `http://monitoring.yourdomain.com:3001/d/application`
- Panels:
  - Business metrics (bookings, payments)
  - User activity
  - Feature usage
  - API endpoint performance

## Log Analysis

### Accessing Logs

1. **Kibana Interface:**
   ```
   URL: http://monitoring.yourdomain.com:5601
   Index: logstash-pafar-*
   ```

2. **Docker Logs:**
   ```bash
   # View all service logs
   docker-compose -f docker-compose.prod.yml logs
   
   # View specific service logs
   docker-compose -f docker-compose.prod.yml logs backend
   
   # Follow logs in real-time
   docker-compose -f docker-compose.prod.yml logs -f backend
   ```

3. **System Logs:**
   ```bash
   # Application logs
   tail -f /var/log/pafar/application.log
   
   # Nginx logs
   tail -f /var/log/nginx/access.log
   tail -f /var/log/nginx/error.log
   ```

### Common Log Queries

1. **Error Analysis:**
   ```
   level:ERROR AND @timestamp:[now-1h TO now]
   ```

2. **Performance Issues:**
   ```
   response_time:>5000 AND @timestamp:[now-1h TO now]
   ```

3. **Authentication Failures:**
   ```
   message:"authentication failed" AND @timestamp:[now-24h TO now]
   ```

4. **Payment Issues:**
   ```
   service:payment AND level:ERROR AND @timestamp:[now-1h TO now]
   ```

## Alert Configuration

### Critical Alerts (Immediate Response)

1. **Service Down:**
   ```yaml
   alert: ServiceDown
   expr: up{job="pafar-backend"} == 0
   for: 1m
   severity: critical
   ```

2. **High Error Rate:**
   ```yaml
   alert: HighErrorRate
   expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
   for: 5m
   severity: critical
   ```

3. **Database Connection Issues:**
   ```yaml
   alert: DatabaseConnectionHigh
   expr: pg_stat_database_numbackends > 80
   for: 2m
   severity: critical
   ```

### Warning Alerts (Monitor Closely)

1. **High Response Time:**
   ```yaml
   alert: HighResponseTime
   expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
   for: 10m
   severity: warning
   ```

2. **High Memory Usage:**
   ```yaml
   alert: HighMemoryUsage
   expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
   for: 5m
   severity: warning
   ```

## Troubleshooting Procedures

### High CPU Usage
1. **Identify the cause:**
   ```bash
   # Check container CPU usage
   docker stats --no-stream
   
   # Check system processes
   top -p $(docker inspect -f '{{.State.Pid}}' container_name)
   ```

2. **Investigate application:**
   ```bash
   # Check for long-running queries
   docker-compose exec db psql -U $POSTGRES_USER -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
   
   # Check application logs for errors
   docker-compose logs backend | grep ERROR
   ```

3. **Scale if needed:**
   ```bash
   # Scale backend service
   docker-compose -f docker-compose.prod.yml up -d --scale backend=3
   ```

### Memory Leaks
1. **Monitor memory usage:**
   ```bash
   # Check memory usage over time
   docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
   ```

2. **Analyze heap dumps:**
   ```bash
   # Generate heap dump (if using Python memory profiler)
   docker-compose exec backend python -m memory_profiler app/main.py
   ```

3. **Restart services if needed:**
   ```bash
   docker-compose -f docker-compose.prod.yml restart backend
   ```

### Database Performance Issues
1. **Check slow queries:**
   ```sql
   SELECT query, mean_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   ```

2. **Check locks:**
   ```sql
   SELECT * FROM pg_locks 
   WHERE NOT granted;
   ```

3. **Analyze query plans:**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM bookings WHERE user_id = 'uuid';
   ```

### Network Issues
1. **Check connectivity:**
   ```bash
   # Test internal service connectivity
   docker-compose exec backend curl -f http://db:5432
   
   # Test external connectivity
   curl -f https://api.stripe.com
   ```

2. **Check DNS resolution:**
   ```bash
   # Test DNS resolution
   nslookup yourdomain.com
   
   # Check container DNS
   docker-compose exec backend nslookup db
   ```

## Performance Optimization

### Database Optimization
1. **Index analysis:**
   ```sql
   SELECT schemaname, tablename, attname, n_distinct, correlation 
   FROM pg_stats 
   WHERE tablename = 'bookings';
   ```

2. **Connection pooling:**
   ```bash
   # Check connection pool status
   docker-compose exec backend python -c "from app.core.database import engine; print(engine.pool.status())"
   ```

### Application Optimization
1. **Cache hit rates:**
   ```bash
   # Redis cache statistics
   docker-compose exec redis redis-cli info stats
   ```

2. **API response times:**
   ```bash
   # Test API endpoints
   curl -w "@curl-format.txt" -o /dev/null -s https://yourdomain.com/api/health
   ```

## Backup and Recovery Monitoring

### Backup Status
1. **Check backup completion:**
   ```bash
   # Check last backup
   ls -la /var/backups/postgresql/
   
   # Verify backup integrity
   gunzip -t /var/backups/postgresql/latest.sql.gz
   ```

2. **Monitor backup logs:**
   ```bash
   tail -f /var/log/postgres-backup.log
   ```

### Recovery Testing
1. **Test restore procedure:**
   ```bash
   # Test restore on staging
   ./scripts/postgres-restore.sh --dry-run latest
   ```

## Emergency Response

### Service Outage
1. **Immediate actions:**
   - Check service status in Grafana
   - Review recent deployments
   - Check system resources
   - Review error logs

2. **Communication:**
   - Update status page
   - Notify stakeholders
   - Post in incident channel

3. **Recovery:**
   - Implement fix or rollback
   - Monitor recovery
   - Post-incident review

### Data Corruption
1. **Stop affected services:**
   ```bash
   docker-compose -f docker-compose.prod.yml stop backend celery-worker
   ```

2. **Assess damage:**
   ```bash
   # Check database integrity
   docker-compose exec db pg_dump --schema-only $POSTGRES_DB > schema_check.sql
   ```

3. **Restore from backup:**
   ```bash
   ./scripts/postgres-restore.sh latest
   ```

## Contact Information
- **On-call Engineer**: +1-xxx-xxx-xxxx
- **DevOps Team**: devops@company.com
- **Incident Channel**: #pafar-incidents
- **Status Page**: https://status.yourdomain.com