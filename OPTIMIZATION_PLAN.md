# Production Optimization Plan for Hetzner AX41-NVMe

## Hardware Profile
- **CPU**: AMD Ryzen 5 3600 (6 cores, 12 threads @ 3.6-4.2 GHz)
- **RAM**: 64 GB DDR4
- **Storage**: 2x 512 GB NVMe SSDs (RAID1 recommended)
- **Network**: Gigabit Ethernet

---

## 1. RESOURCE ALLOCATION STRATEGY

### Target Allocation (64 GB Total)
```
Database (PostgreSQL)      → 24 GB
Caching (Redis)           →  4 GB
Message Broker (RabbitMQ) →  4 GB
Application Services      → 16 GB (shared among 5 services)
  - Backend              →  4 GB
  - Chat-Room           →  3 GB
  - Data-Pipeline       →  4 GB
  - Notifications       →  2 GB
  - Landing Service     →  2 GB
  - Frontend            →  1 GB
System/Kernel Reserved   → 12 GB
```

### CPU Allocation (6 cores / 12 threads)
```
- PostgreSQL:        2-3 cores (max_parallel_workers = 4, max_worker_processes = 4)
- RabbitMQ:         1 core (for broker operations)
- Redis:            0.5 cores (mostly I/O bound)
- Applications:     3-4 cores (combined workers)
- System:           Reserved (OS, kernel)
```

---

## 2. POSTGRESQL 16 OPTIMIZATION

### Critical PostgreSQL Settings (for 64GB server with 6 cores)

**Memory Configuration:**
```
shared_buffers = 24GB              # 25% of RAM (was 16GB)
effective_cache_size = 32GB        # 50% of RAM (was not set)
work_mem = 256MB                   # (24GB / max_conn / 4) = 256MB (was 128MB)
maintenance_work_mem = 2GB         # For VACUUM, CREATE INDEX (was default)
```

**Parallelization:**
```
max_parallel_workers_per_gather = 4   # Was not set
max_parallel_maintenance_workers = 3   # Was not set
max_parallel_workers = 6               # Equal to CPU cores
```

**Connection Management:**
```
max_connections = 150              # Increased from 100 (ratio: 150 connections for production)
superuser_reserved_connections = 5 # For emergency access
```

**WAL & Checkpoints:**
```
max_wal_size = 8GB                 # Increased from 4GB (better batching)
min_wal_size = 1GB                 # Increased from 512MB
checkpoint_timeout = 5min          # Default (optimized)
checkpoint_completion_target = 0.9 # Keep as is
```

**Logging & Monitoring:**
```
log_min_duration_statement = 500    # Log queries > 500ms (increased from 250ms)
log_statement = 'mod'              # Log DDL & DML only (not SELECT)
log_connections = on               # Track connections
log_disconnections = on             # Track disconnections
log_duration = off                 # Let log_min_duration_statement handle it
```

**Query Performance:**
```
random_page_cost = 1.1             # NVMe is fast (was default 4.0)
effective_io_concurrency = 200     # NVMe SSDs support high concurrency
join_collapse_limit = 12           # Allow complex joins (was 8)
from_collapse_limit = 12           # For subqueries (was 8)
```

**Autovacuum Tuning:**
```
autovacuum_max_workers = 4         # Was default (3)
autovacuum_naptime = 30s           # Check every 30s (was 1min)
autovacuum_vacuum_cost_limit = 500 # Increase throughput (was -1/2ms default)
autovacuum_analyze_scale_factor = 0.05  # Analyze more aggressive
autovacuum_vacuum_scale_factor = 0.1    # Vacuum more aggressive
```

---

## 3. RABBITMQ OPTIMIZATION

### RabbitMQ Configuration (4GB allocated)

Create/Update `/rabbitmq-init/rabbitmq.conf`:
```properties
# Memory limits
vm_memory_high_watermark.relative = 0.3    # 30% of container limit
vm_memory_high_watermark_paging_ratio = 0.75

# Networking
listeners.tcp.default = 5672
management.tcp.port = 15672
heartbeat = 60

# Performance
channel_max = 2048
connection_max = unlimited
frame_max = 131072

# Disk & Queue settings
total_memory_available_override = 4GB
disk_free_limit.absolute = 2GB

# Logging
log.file.level = warning
log.console.level = warning
log.console = true

# Monitoring
collect_statistics_interval = 10000
```

Docker Compose limits:
```yaml
resources:
  limits:
    cpus: '1'          # 1 CPU core
    memory: 4G
  reservations:
    cpus: '0.8'
    memory: 3G
```

---

## 4. REDIS OPTIMIZATION

### Redis Configuration (4GB allocated)

Create `/redis-config/redis.conf`:
```conf
# Memory management
maxmemory 4gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Network
timeout 300
tcp-backlog 500
tcp-keepalive 60

# Performance
databases 16
io-threads 4           # Match available cores
io-threads-do-reads yes

# Logging
loglevel warning

# Client output buffering
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
```

Docker Compose limits:
```yaml
resources:
  limits:
    cpus: '0.5'
    memory: 4G
  reservations:
    cpus: '0.3'
    memory: 3G
```

---

## 5. APPLICATION SERVICES OPTIMIZATION

### Gunicorn/Uvicorn Configuration

For each Python application (backend, chat-room, notifications, data-pipeline):

```python
# gunicorn.conf.py
import multiprocessing

# Worker configuration
workers = min(4, multiprocessing.cpu_count())  # 4 workers max
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
worker_timeout = 30
max_requests = 1000
max_requests_jitter = 50

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Logging
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(q)s"'
accesslog = "-"
errorlog = "-"
loglevel = "warning"

# Server hooks
def on_starting(server):
    print("Gunicorn server is starting")

def when_ready(server):
    print("Gunicorn server is ready for requests")
```

### Docker Compose Resource Limits

**Backend Service (4GB)**:
```yaml
resources:
  limits:
    cpus: '1.5'
    memory: 4G
  reservations:
    cpus: '1'
    memory: 2.5G
```

**Chat-Room Service (3GB)**:
```yaml
resources:
  limits:
    cpus: '1'
    memory: 3G
  reservations:
    cpus: '0.75'
    memory: 2G
```

**Data-Pipeline Service (4GB)**:
```yaml
resources:
  limits:
    cpus: '1.5'
    memory: 4G
  reservations:
    cpus: '1'
    memory: 2.5G
```

**Notifications Service (2GB)**:
```yaml
resources:
  limits:
    cpus: '0.5'
    memory: 2G
  reservations:
    cpus: '0.3'
    memory: 1G
```

**Landing Service (2GB)**:
```yaml
resources:
  limits:
    cpus: '0.5'
    memory: 2G
  reservations:
    cpus: '0.3'
    memory: 1G
```

**Frontend (1GB)**:
```yaml
resources:
  limits:
    cpus: '0.25'
    memory: 1G
  reservations:
    cpus: '0.1'
    memory: 512M
```

---

## 6. OS-LEVEL TUNING (Linux Kernel)

### TCP/Network Tuning (`/etc/sysctl.conf`)

```bash
# Network performance
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 5000

# Connection handling
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 3

# File descriptors
fs.file-max = 2097152
fs.nr_open = 2097152

# IPC
kernel.shmmax = 34359738368
kernel.shmall = 8388608
```

### File Descriptor Limits (`/etc/security/limits.conf`)

```
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
```

---

## 7. CONTAINER ORCHESTRATION & HEALTHCHECKS

### Improved Healthchecks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "--max-time", "3", "http://localhost:8000/health"]
  interval: 10s        # Check every 10s (was 30s)
  timeout: 5s          # Timeout after 5s (was 10s)
  retries: 2           # Fail after 2 retries (was 3)
  start_period: 20s    # Wait 20s before checking (initial startup)
```

### Restart Policies

```yaml
# For critical services
restart: always
# With delay for cascade recovery
restart: on-failure
restart_policy:
  condition: on-failure
  delay: 5s
  max_attempts: 5
  window: 120s
```

---

## 8. MONITORING & OBSERVABILITY

### Key Metrics to Monitor

**Database:**
- `pg_stat_statements.mean_exec_time` - Slow queries
- `pg_stat_statements.calls` - Query frequency
- `transactions` - TPS (transactions per second)
- `active_connections` - Connection count
- `cache_hit_ratio` - Should be > 99%

**Memory:**
- `process_resident_memory_bytes` - Actual memory usage
- `container_memory_usage_bytes` - Docker memory usage
- RabbitMQ queue depth
- Redis memory usage

**CPU:**
- `node_cpu_seconds_total` - CPU usage
- Process CPU time
- I/O wait percentage

**Application:**
- Response times (p95, p99)
- Error rates
- Request rate

### Prometheus Configuration

Update `monitoring/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'production'

scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

---

## 9. IMPLEMENTATION CHECKLIST

### Phase 1: Preparation
- [ ] Backup current database and configurations
- [ ] Create separate PostgreSQL configuration file for production
- [ ] Create Redis configuration file
- [ ] Test configurations on staging

### Phase 2: Database Updates
- [ ] Update `postgresql.conf` with optimized settings
- [ ] Restart PostgreSQL
- [ ] Run `VACUUM ANALYZE` on all tables
- [ ] Monitor `pg_stat_statements` for slow queries
- [ ] Adjust `log_min_duration_statement` as needed

### Phase 3: Service Containers
- [ ] Update docker-compose.prod.yaml with resource limits
- [ ] Update Gunicorn configurations
- [ ] Update RabbitMQ configuration
- [ ] Update Redis configuration
- [ ] Test services individually

### Phase 4: System Configuration
- [ ] Apply sysctl settings
- [ ] Update file descriptor limits
- [ ] Verify settings with `sysctl -a | grep ...`

### Phase 5: Monitoring & Validation
- [ ] Verify Prometheus scrapes all targets
- [ ] Create Grafana dashboards
- [ ] Monitor metrics for 24-48 hours
- [ ] Adjust resource limits based on actual usage
- [ ] Set up alerts for anomalies

---

## 10. PERFORMANCE EXPECTATIONS

After optimization, expect:

| Metric | Current | Expected |
|--------|---------|----------|
| Database Throughput | Unknown | 5,000+ TPS |
| Query Response Time | Unknown | <50ms (p95) |
| Cache Hit Ratio | Unknown | >99% |
| Memory Usage | Unmanaged | Stable at 45-55GB |
| CPU Utilization | Unmanaged | 40-60% average |
| Connection Pool | 100 | 150 active |

---

## 11. TROUBLESHOOTING GUIDE

### PostgreSQL Issues
- **High `shared_buffers` causing issues**: Reduce gradually (24GB → 18GB → 14GB)
- **Slow queries**: Enable `pg_stat_statements` extension and analyze
- **Memory errors**: Check `work_mem` × `max_connections` / 4 = sum
- **Autovacuum lag**: Increase `autovacuum_max_workers` or tune costs

### Application Issues
- **Out of memory**: Reduce worker count or service `memory` limit
- **Connection pool exhausted**: Increase `max_connections` in PostgreSQL
- **Slow response times**: Check `log_min_duration_statement` logs
- **High CPU**: Profile applications with `py-spy` or `cProfile`

### Docker Issues
- **Container crashes**: Check CloudWatch logs and OOM killer
- **Disk space**: Monitor `/var/lib/docker/` and NVMe usage
- **Network timeouts**: Verify `tcp_fin_timeout` and firewall rules

---

## 12. SCALING CONSIDERATIONS FOR FUTURE

**Vertical Scaling (Current Server):**
- Max out to 128GB RAM upgrade
- Profile data-pipeline to identify bottlenecks
- Consider separate PostgreSQL server if DB load > 70%

**Horizontal Scaling:**
- Plan for read replicas of PostgreSQL
- Use HAProxy for application load balancing
- Consider Redis Cluster for cache scaling
- Use RabbitMQ queue prioritization for task distribution

---

## References
- PostgreSQL 16 Documentation: https://www.postgresql.org/docs/16/
- Gunicorn Best Practices: https://docs.gunicorn.org/en/latest/design.html
- Docker Best Practices: https://docs.docker.com/config/containers/resource_constraints/
- RabbitMQ Tuning: https://www.rabbitmq.com/configure.html
- Redis Configuration: https://redis.io/docs/management/config/
