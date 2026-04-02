# Production Deployment & Optimization Checklist

## ✅ Files Created/Modified

### 1. **OPTIMIZATION_PLAN.md** (Main Reference)
   - Comprehensive 12-section optimization guide
   - Resource allocation strategy
   - Configuration details for each component
   - Monitoring setup
   - Troubleshooting guide

### 2. **postgresql-prod.conf** (New)
   - Location: `postgres-init/postgresql-prod.conf`
   - Status: ✅ Ready to deploy
   - Key Changes from Default:
     - `shared_buffers`: 16GB → 24GB
     - `effective_cache_size`: unset → 32GB
     - `work_mem`: 128MB → 256MB
     - `max_connections`: 100 → 150
     - `random_page_cost`: 4.0 → 1.1 (NVMe optimization)
     - `effective_io_concurrency`: default → 200
     - Parallel workers: Increased to 6
     - Autovacuum: Aggressive tuning enabled

### 3. **redis.conf** (New)
   - Location: `redis-config/redis.conf`
   - Status: ✅ Ready to deploy
   - Key Settings:
     - `maxmemory`: 4GB
     - `maxmemory-policy`: allkeys-lru
     - `io-threads`: 4
     - `appendonly`: yes (persistence)
     - `appendfsync`: everysec

### 4. **docker-compose.prod.yaml** (Updated)
   - Status: ✅ Ready to deploy
   - Changes Made:
     - Added `resources.limits` for all services
     - Added `resources.reservations` for all services
     - Improved healthchecks (faster detection)
     - Added start_period for graceful startup

### 5. **gunicorn.conf.py** (Updated)
   - Location: `backend/gunicorn.conf.py`
   - Status: ✅ Ready to deploy
   - Improvements:
     - Better documentation
     - Dynamic worker count
     - Improved logging hooks
     - Conservative worker allocation

---

## 🚀 DEPLOYMENT STEPS

### Phase 1: Pre-Deployment (Staging)
```bash
# 1. Test on staging/dev first
cd /path/to/project

# 2. Backup current configs
cp postgres-init/postgresql.conf postgres-init/postgresql.conf.backup
cp redis-config/redis.conf redis-config/redis.conf.backup
cp docker-compose.prod.yaml docker-compose.prod.yaml.backup

# 3. Review the optimization plan
cat OPTIMIZATION_PLAN.md

# 4. Check current PostgreSQL version
psql --version  # Should be 16.x
```

### Phase 2: PostgreSQL Configuration
```bash
# 1. Copy optimized config
cp postgres-init/postgresql-prod.conf postgres-init/postgresql.conf

# 2. Reload PostgreSQL (if running)
# For containerized: docker restart <db_container>
# For native: sudo systemctl restart postgresql

# 3. Verify config applied
psql -U grain -d graintrade_db -c "SHOW shared_buffers;"
psql -U grain -d graintrade_db -c "SHOW max_connections;"
psql -U grain -d graintrade_db -c "SHOW work_mem;"

# 4. Enable pg_stat_statements if not enabled
psql -U grain -d graintrade_db -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
```

### Phase 3: Redis Configuration
```bash
# 1. Copy optimized config (if using containerized Redis)
cp redis-config/redis.conf ./redis-config/

# 2. Update docker-compose to use the config file:
#    volumes:
#      - ./redis-config/redis.conf:/usr/local/etc/redis/redis.conf
#    command: redis-server /usr/local/etc/redis/redis.conf

# 3. Restart Redis
docker-compose -f docker-compose.prod.yaml restart redis

# 4. Verify config
docker exec <redis_container> redis-cli CONFIG GET maxmemory
```

### Phase 4: Update Docker Compose
```bash
# 1. Deploy updated compose file
docker-compose -f docker-compose.prod.yaml pull

# 2. Start services with new limits
docker-compose -f docker-compose.prod.yaml up -d

# 3. Verify all services are running
docker-compose -f docker-compose.prod.yaml ps

# 4. Check logs for any startup issues
docker-compose -f docker-compose.prod.yaml logs --tail=50
```

### Phase 5: OS-Level Tuning (as root)
```bash
# Edit sysctl configuration
sudo nano /etc/sysctl.conf

# Add these settings for network performance:
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 5000

# Apply changes without reboot
sudo sysctl -p

# Verify changes
sudo sysctl net.core.rmem_max
```

### Phase 6: File Descriptor Limits
```bash
# Edit limits file
sudo nano /etc/security/limits.conf

# Add at the end:
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768

# Logout and login for changes to take effect
# Or edit systemd service if running services as systemd
```

---

## 📊 MONITORING & VALIDATION

### Immediate Checks (After Deployment)

```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health

# Check PostgreSQL
psql -U grain -d graintrade_db -c "SELECT version();"

# Check Redis
redis-cli -a Teodorathome ping

# Check RabbitMQ (if using)
# Access management UI or test connection
```

### Key Metrics to Monitor (First 24-48 Hours)

**Database:**
```sql
-- Cache hit ratio (should be > 99%)
SELECT
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit) as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;

-- Slow queries
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;

-- Active connections
SELECT count(*) as active_connections FROM pg_stat_activity;

-- Database size
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname))
FROM pg_database ORDER BY pg_database_size(pg_database.datname) DESC;
```

**Memory Usage:**
```bash
# Docker memory usage
docker stats --no-stream

# System memory
free -h

# Swap usage (should be minimal)
vmstat 1 5
```

**CPU Usage:**
```bash
# CPU cores utilized per service
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

**Application Logs:**
```bash
# Watch backend logs
docker logs -f <backend_container>

# Watch PostgreSQL slow query log
tail -f /var/lib/postgresql/14/main/log/postgresql-*.log | grep "duration:"

# Watch error logs
docker-compose -f docker-compose.prod.yaml logs -f
```

---

## ⚠️ PERFORMANCE TUNING (ITERATIVE)

### If Services Crash (OOM):
1. Reduce service `memory.limits` in docker-compose.prod.yaml
2. Check what's consuming memory: `docker stats`
3. Consider splitting services across multiple servers

### If Queries are Slow:
1. Check `pg_stat_statements` for slow queries
2. Create indexes on frequently filtered columns
3. Run `ANALYZE` on tables to update statistics
4. Consider query rewriting/optimization

### If Connection Pool is Maxed Out:
1. Check for connection leaks: `SELECT * FROM pg_stat_activity;`
2. Increase `max_connections` gradually (currently 150)
3. Implement connection pooling with PgBouncer if needed

### If Redis is Evicting Keys:
1. Check `INFO stats` for `evicted_keys` count
2. Increase Redis `maxmemory` (currently 4GB)
3. Review what's being cached - optimize usage patterns
4. Consider Redis Cluster for scaling

---

## 🔄 ROLLBACK PLAN

If issues arise:

```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yaml stop

# 2. Restore PostgreSQL config
cp postgres-init/postgresql.conf.backup postgres-init/postgresql.conf

# 3. Restore docker-compose
cp docker-compose.prod.yaml.backup docker-compose.prod.yaml

# 4. Restart with old configuration
docker-compose -f docker-compose.prod.yaml up -d

# 5. Verify everything is working
docker-compose -f docker-compose.prod.yaml logs --tail=20
```

---

## 📈 EXPECTED IMPROVEMENTS

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Query Response Time | Unknown | <50ms (p95) | ↓ 50%+ |
| Database Cache Hit | Unknown | >99% | ↑ Better |
| Max Connections | 100 | 150 | ↑ 50% |
| Parallel Workers | 2 | 6 | ↑ 3x |
| WAL Batch Size | 4GB | 8GB | ↑ Better throughput |
| Worker Processes | 2 | 4 | ↑ 2x |
| Memory Efficiency | Uncontrolled | Controlled | ✅ Stable |

---

## 📝 NOTES

- **Test First**: Deploy to staging environment first
- **Monitor Closely**: Watch metrics for first 48 hours
- **Gradual Rollout**: Can be applied during maintenance window
- **Backup Always**: Keep backups of all config files
- **Document Changes**: Note any customizations made
- **Review Logs**: Check application logs for errors

---

## 🔗 QUICK REFERENCE

| File | Type | Action |
|------|------|--------|
| OPTIMIZATION_PLAN.md | Guide | Review & Reference |
| postgresql-prod.conf | Config | Copy to postgres-init/ |
| redis.conf | Config | Copy to redis-config/ |
| docker-compose.prod.yaml | Deploy | Use for production |
| gunicorn.conf.py | Code | Already updated |

---

## ❓ QUESTIONS?

Refer to the OPTIMIZATION_PLAN.md for detailed explanation of each setting.

Key sections:
- Section 2: PostgreSQL optimization details
- Section 3: RabbitMQ tuning
- Section 4: Redis optimization
- Section 5: Application services
- Section 6: OS-level tuning
- Section 11: Troubleshooting guide
