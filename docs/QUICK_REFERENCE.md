# Production Configuration Quick Reference

## 🎯 Quick Adjustment Guide

### PostgreSQL Tuning (most impactful)

**If queries are slow:**
```sql
-- Check top slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;

-- Check missing indexes
SELECT indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE idx_scan = 0;

-- Reset statistics
SELECT pg_stat_statements_reset();
```

**Cache hit ratio too low (< 99%):**
- Increase `shared_buffers` (currently 24GB)
- Check with: `SELECT heap_blks_hit::float / (heap_blks_hit + heap_blks_read) FROM pg_statio_user_tables;`
- If still low: might need more RAM or better queries

**Connections maxed out (150):**
- Don't blindly increase; find connection leaks first
- Check: `SELECT state, count(*) FROM pg_stat_activity GROUP BY state;`
- Use PgBouncer for connection pooling if needed

---

### Memory Optimization

**Container running OOM:**
1. Check actual usage: `docker stats <container>`
2. Reduce limits in docker-compose.prod.yaml
3. Profile application: `docker exec <container> pip install py-spy`
4. Consider splitting services

**Redis evicting keys:**
- Check: `redis-cli INFO stats | grep evicted`
- Options:
  1. Increase maxmemory (4GB → 6GB max)
  2. Remove unused keys
  3. Reduce TTL values
  4. Use Redis Cluster for scaling

---

### CPU Tuning

**High CPU usage (>70%):**
- Check which service: `docker stats`
- Profile Python app: `docker exec <id> pip install py-spy && py-spy record -o profile.svg -d 30 -- python app.py`
- Optimize slow functions, reduce logging

**Worker processes insufficient:**
- Current: 4 per backend
- Check: `ps aux | grep gunicorn`
- Increase cautiously (watch memory)

---

### I/O Optimization

**Slow disk performance:**
- Check: `iostat -x 1 10` (Linux utility)
- MongoDB/database slow: check indexes
- Check NVMe health: `sudo nvme smart-log /dev/nvme0n1`

**WAL growing too fast:**
- Symptom: `max_wal_size` exceeded frequently
- Solution: Increase `log_checkpoints = on` and analyze
- Check: `SELECT * FROM pg_stat_bgwriter;`

---

## 📊 Monitoring Dashboard Queries

### Create a monitoring view in PostgreSQL:

```sql
-- Overall system health
SELECT 
  (SELECT count(*) FROM pg_stat_activity) as active_connections,
  (SELECT setting::bigint FROM pg_settings WHERE name='max_connections') as max_connections,
  pg_database_size('graintrade_db') as database_size,
  (SELECT sum(heap_blks_hit)::float / nullif(sum(heap_blks_hit + heap_blks_read), 0) 
   FROM pg_statio_user_tables) as cache_hit_ratio;

-- Transaction throughput
SELECT 
  xact_commit as transactions_committed,
  xact_rollback as transactions_rolled_back,
  (xact_commit + xact_rollback) as total_tps,
  stats_reset
FROM pg_stat_database 
WHERE datname = 'graintrade_db';

-- Slow query log
SELECT 
  query,
  mean_exec_time,
  max_exec_time,
  calls,
  total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC 
LIMIT 20;
```

---

## 🔧 Configuration File Locations

| Service | Config File | Container Path |
|---------|-------------|-----------------|
| PostgreSQL | `postgres-init/postgresql-prod.conf` | `/etc/postgresql/16/main/postgresql.conf` |
| Redis | `redis-config/redis.conf` | `/usr/local/etc/redis/redis.conf` |
| Gunicorn | `backend/gunicorn.conf.py` | Inside container |
| Docker | `docker-compose.prod.yaml` | N/A |

---

## 🚨 Emergency Procedures

### PostgreSQL Crisis Mode
```bash
# Immediate actions if database is slow:
1. Kill long-running queries:
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
   WHERE duration > '1 hour'::interval;

2. Force vacuum:
   VACUUM ANALYZE; -- Run during low traffic

3. Reset cache:
   DISCARD PLANS; -- Clear statement cache

4. Check bloat:
   SELECT * FROM pg_stat_all_tables 
   WHERE n_live_tup > 0 
   ORDER BY n_dead_tup DESC;
```

### Redis Recovery
```bash
# If Redis is consuming too much memory
redis-cli MEMORY DOCTOR

# Clear unused keys
redis-cli CONFIG SET maxmemory-policy volatile-lru
redis-cli FLUSHDB -- last resort, will lose data

# Check persistence
redis-cli BGSAVE
redis-cli LASTSAVE
```

### Container Recovery
```bash
# Restart chronically crashing service
docker-compose -f docker-compose.prod.yaml restart <service_name>

# Remove and recreate
docker-compose -f docker-compose.prod.yaml down <service_name>
docker-compose -f docker-compose.prod.yaml up -d <service_name>

# Check for restart loops
docker events --type=container | grep -i restart
```

---

## 📈 Scaling Decision Matrix

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU Avg > 80% | Sustained | Add worker processes or split service |
| Memory > 80% | Any time | Reduce service limits or upgrade RAM |
| DB Connections > 120 | Sustained | Add connection pooling (PgBouncer) |
| Query p99 > 100ms | Frequent | Profile & optimize queries/indexes |
| Redis eviction > 100/sec | Any time | Increase maxmemory or reduce TTL |
| Disk usage > 80% | Any time | Archive logs, optimize tables |

---

## 🔍 Diagnostic Commands

```bash
# PostgreSQL diagnostics
psql -U grain -d graintrade_db -c "\d+"  # Table sizes
psql -U grain -d graintrade_db -c "SHOW all;" | grep -i shared

# Redis diagnostics  
redis-cli INFO all
redis-cli --latency
redis-cli SLOWLOG GET 10

# Docker diagnostics
docker-compose -f docker-compose.prod.yaml logs --since 1h
docker stats --no-stream
docker top <container_id>

# System diagnostics
free -h              # Memory
top -b -n 1          # Processes
iostat -d 1 5        # I/O
netstat -an | grep ESTABLISHED | wc -l  # Connections
```

---

## 💡 Pro Tips

1. **Regular Backups**: `pg_dump graintrade_db > backup.sql` (daily)
2. **Index Maintenance**: `REINDEX DATABASE graintrade_db;` (monthly)
3. **Stats Update**: `ANALYZE;` (weekly)
4. **Log Rotation**: Check `log_rotation_size` and `log_rotation_age`
5. **Connection Pooling**: Consider PgBouncer if connections exceed 200
6. **Cache Warming**: Pre-load hot data: `SELECT * FROM large_table LIMIT 1000;`

---

## 📚 Configuration Parameter Impact

| Parameter | Default → Optimized | Impact |
|-----------|-------------------|--------|
| shared_buffers | 128MB → 24GB | 🔥 High (cache efficiency) |
| work_mem | 4MB → 256MB | 🔥 High (query performance) |
| random_page_cost | 4.0 → 1.1 | 🔴 High (query plans) |
| effective_io_concurrency | 1 → 200 | 🟠 Medium (parallel queries) |
| max_parallel_workers | 8 → 6 | 🟠 Medium (CPU utilization) |
| autovacuum_naptime | 60s → 30s | 🟡 Low (bloat prevention) |

---

## ⚙️ Restart Procedures

```bash
# Graceful PostgreSQL restart
sudo systemctl reload postgresql

# Or for Docker
docker-compose -f docker-compose.prod.yaml restart db

# Verify
psql -U grain -d graintrade_db -c "SELECT version();"
```

---

## 🎓 Learning Resources

- PostgreSQL Tuning: https://wiki.postgresql.org/wiki/Performance_Optimization
- Redis Optimization: https://redis.io/docs/management/optimization/
- Docker Best Practices: https://docs.docker.com/config/containers/resource_constraints/
- Linux Tuning: https://www.kernel.org/doc/html/latest/networking/ip-sysctl.html
