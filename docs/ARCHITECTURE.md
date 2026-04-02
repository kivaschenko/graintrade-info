# Production Architecture & Resource Allocation

## 📊 Hardware Specifications
```
┌─────────────────────────────────────────────────────────────┐
│         HETZNER AX41-NVMe DEDICATED SERVER                   │
│  AMD Ryzen 5 3600 (6C/12T) | 64GB DDR4 | 2x 512GB NVMe SSD  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Container Architecture & Resource Allocation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PROD DOCKER COMPOSE (64GB Total)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    INFRASTRUCTURE SERVICES                      │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │ 📊 Prometheus    │ 1.0 GB │ 0.5 CPU │ Metrics collection       │    │
│  │ 🖼️  Grafana       │ 1.0 GB │ 0.5 CPU │ Dashboard visualization │    │
│  │ 📈 Node Exporter │ 0.3 GB │ 0.25 CPU│ System metrics          │    │
│  │ PG Exporter      │ 0.3 GB │ 0.25 CPU│ DB metrics              │    │
│  │ Redis Exporter   │ 0.3 GB │ 0.25 CPU│ Cache metrics           │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │ Subtotal: ~3 GB RAM, ~2 CPU cores (monitoring)                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    APPLICATION SERVICES                        │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │ 🟦 Backend            │ 4.0 GB │ 1.5 CPU │ FastAPI Core API    │    │
│  │    - Workers: 4       │        │         | Async I/O-heavy     │    │
│  │    - Timeout: 30s     │        │         │                    │    │
│  │                                                                  │    │
│  │ 💬 Chat-Room         │ 3.0 GB │ 1.0 CPU │ WebSocket chat      │    │
│  │    - Workers: 4       │        │         │ Real-time messaging │    │
│  │                                                                  │    │
│  │ 📧 Notifications     │ 2.0 GB │ 0.5 CPU │ Email/SMS sender    │    │
│  │    - Workers: 2       │        │         │ Queue processor     │    │
│  │                                                                  │    │
│  │ 📈 Data-Pipeline     │ 4.0 GB │ 1.5 CPU │ Analytics/ML        │    │
│  │    - Workers: 4       │        │         │ CPU-intensive       │    │
│  │                                                                  │    │
│  │ 🏠 Landing Service    │ 2.0 GB │ 0.5 CPU │ Static/Marketing    │    │
│  │    - Lightweight      │        │         │ Simple HTTP         │    │
│  │                                                                  │    │
│  │ 🌐 Frontend (Nginx)   │ 1.0 GB │ 0.25 CPU│ Vue.js SPA          │    │
│  │    - Reverse proxy    │        │         │ Static files        │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │ Subtotal: 16 GB RAM, 5.25 CPU cores                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                  CORE EXTERNAL SERVICES                         │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │ 🗄️  PostgreSQL 16 with PostGIS                                  │    │
│  │     Memory: 24 GB (shared_buffers + cache)                     │    │
│  │     CPU: 2-3 cores (parallel workers)                          │    │
│  │     Features:                                                   │    │
│  │       • shared_buffers: 24GB (25% of RAM)                      │    │
│  │       • effective_cache_size: 32GB                             │    │
│  │       • work_mem: 256MB (sorts/joins)                          │    │
│  │       • max_connections: 150                                   │    │
│  │       • max_parallel_workers: 6                                │    │
│  │       • Cache hit ratio target: >99%                           │    │
│  │                                                                  │    │
│  │ 🔴 Redis 7.4 (Persistent Cache)                                │    │
│  │     Memory: 4 GB (maxmemory)                                   │    │
│  │     CPU: 0.5 cores (I/O bound)                                 │    │
│  │     Features:                                                   │    │
│  │       • maxmemory-policy: allkeys-lru                          │    │
│  │       • appendonly: yes (AOF persistence)                      │    │
│  │       • io-threads: 4 (async I/O)                              │    │
│  │       • Target hit rate: >90%                                  │    │
│  │                                                                  │    │
│  │ 🐰 RabbitMQ 4.x (Message Broker)                               │    │
│  │     Memory: 4 GB (vm_memory_high_watermark)                    │    │
│  │     CPU: 1 core (broker overhead)                              │    │
│  │     Features:                                                   │    │
│  │       • Async task queue                                       │    │
│  │       • Durable message delivery                               │    │
│  │       • Consumer prefetch tuning                               │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │ Subtotal: 32 GB RAM, 3.5-4.5 CPU cores                         │    │
│  │ (External to Docker, managed separately)                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                           │
├─────────────────────────────────────────────────────────────────────────┤
│  TOTAL ALLOCATION:                                                      │
│  • Docker Containers:  19 GB RAM + External Services: 32 GB            │
│  • Total Used:         ~51 GB (79% of available)                       │
│  • Reserved for OS:    ~13 GB (21% of available)                       │
│  • CPU Assignment:     ~5.25 Docker + 3.5-4.5 External = 9 cores max  │
│                        (System can burst to 12 threads)                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Network Connectivity Map

```
                        ┌──────────────────┐
                        │  Client/Browser  │
                        └────────┬─────────┘
                                 │ HTTPS:443
                    ┌────────────▼─────────────┐
                    │  Frontend (Nginx:8080)   │  [1GB | 0.25 CPU]
                    └────────────┬─────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
          (HTTP:8000)     (HTTP:8001)     (HTTP:8004)
                 │               │               │
    ┌────────────▼──────┐ │ ┌────────────▼──────┐  [3GB | 1CPU]
    │  Backend API      │ │ │ Chat-Room         │
    │  (FastAPI)        │ │ │ (WebSocket)       │
    [4GB | 1.5 CPU]     │ │ │                   │
    └────────────┬──────┘ │ └────────────┬──────┘
                 │        │              │
                 └────────┼──────────────┘
                          │
           ┌──────────────┼──────────────┬──────────────┐
           │              │              │              │
      [PostgreSQL]   [Redis]       [RabbitMQ]     [Exports]
      [24GB|2-3CPU] [4GB|0.5CPU]  [4GB|1CPU]
      Port: 5433    Port: 6379   Port: 5672
           │              │              │
           └──────────────┼──────────────┘
                    (Local Host)

Legend:
 • Internal Docker Network: 172.18.0.0/16
 • External Services: Using docker host gateway
 • All inter-service communication: HTTP/TCP
 • Database connections: PostgreSQL protocol
 • Cache access: Redis protocol
 • Message broker: AMQP protocol
```

---

## 📈 Request Flow Architecture

```
User Request → Frontend (Nginx) → Backend API
                                    ├→ PostgreSQL (query data)
                                    ├→ Redis (cache check/set)
                                    └→ RabbitMQ (async tasks)

Chat Request → Chat-Room Service → WebSocket Upgrade
                                    ├→ PostgreSQL (chat history)
                                    └→ Redis (session data)

Pipeline Job → Data-Pipeline Service → PostgreSQL (load data)
                                       ├→ Redis (job state)
                                       └→ RabbitMQ (distribute work)

Async Event → RabbitMQ Queue → Notifications Service
                                ├→ Redis (template cache)
                                └→ PostgreSQL (send logs)
```

---

## 💾 Storage Layout

```
/dev/nvme0n1 (512 GB) - Primary (System + Data)
├── / (OS + Docker images)
├── /var/lib/postgresql/14/main/ [PostgreSQL data]
└── /var/lib/docker/ [Docker volumes & containers]

/dev/nvme1n1 (512 GB) - Secondary (Recommended for backups/WAL)
├── PostgreSQL WAL archives
├── Database backups
└── Redis snapshots (RDB files)
```

---

## 🔐 Security Considerations

| Component | Port | Network | Auth | TLS |
|-----------|------|---------|------|-----|
| Frontend | 8080 | Public | None | Nginx SSL |
| Backend | 8000 | Internal | JWT | Optional |
| Chat-Room | 8001 | Internal | JWT | Optional |
| Notifications | 8002 | Internal | API Key | Optional |
| Data-Pipeline | 8004 | Internal | None | Optional |
| PostgreSQL | 5433 | Local | Password | Consider SSL |
| Redis | 6379 | Local | Password | Recommended |
| RabbitMQ | 5672 | Local | Username/Pass | Recommended |
| Prometheus | 9090 | Internal | None | Firewall only |
| Grafana | 3000 | Internal | Login | Nginx reverse proxy |

---

## 🎯 Performance Targets

| Metric | Target | Method |
|--------|--------|--------|
| API Response Time | <50ms (p95) | Application profiling |
| Database Queries | <100ms | Index optimization, EXPLAIN |
| Cache Hits | >90% | Redis INFO stats |
| DB Cache Hit Ratio | >99% | pg_stat_statements |
| Throughput | 1000+ req/sec | Load testing |
| Memory Efficiency | 79% utilized | monitoring/docker stats |
| CPU Efficiency | 40-60% average | monitoring/top |
| Uptime | 99.5%+ | Health checks, auto-restart |

---

## 🚀 Scaling Strategy

### Phase 1: Single Server Optimization (Current)
- ✅ Resource limits applied
- ✅ Database optimization enabled
- ✅ Connection pooling ready
- **Target**: Handle 5K-10K concurrent users

### Phase 2: Read Replicas (500K+ DB operations/day)
```
Primary PostgreSQL → Replica 1 (Read-only)
                  → Replica 2 (Read-only)
                  
Backend queries: Primary server
Analytics queries: Replica servers
```

### Phase 3: Application Clustering (100K+ concurrent users)
```
Load Balancer (HAProxy)
├→ Server 1 (Backend + App stack)
├→ Server 2 (Backend + App stack)
└→ Server 3 (Backend + App stack)

Shared:
├→ PostgreSQL Cluster
├→ Redis Cluster  
└→ RabbitMQ Cluster
```

### Phase 4: Microservices & Kubernetes
- Separate services onto different machines
- Use Kubernetes for orchestration
- Implement caching layers (CDN, Varnish)
- Database sharding by tenant/region

---

## 🔄 Backup & Disaster Recovery

**PostgreSQL Backups:**
```bash
# Full backup (daily)
pg_dump -U grain graintrade_db > backup_$(date +%Y%m%d).sql.gz

# Incremental (WAL archiving)
Archive location: /mnt/backups/wal_archive/
Retention: 30 days
```

**Redis Snapshots:**
```bash
# RDB snapshots (automatic at configured intervals)
- /var/lib/redis/dump.rdb
- Frequency: After 900s + 1 change, 300s + 10 changes, 60s + 10000 changes

# AOF log (real-time)
- /var/lib/redis/appendonly.aof
- Fsync: Every second
```

**Recovery Time Objectives (RTO):**
- Application containers: 2-5 minutes
- Database: 10-30 minutes (depends on backup size)
- Full system: 30-60 minutes

---

## 📊 Monitoring Stack

```
┌────────────────────────────┐
│    Prometheus (9090)       │  ← Scrapes every 15s
├────────────────────────────┤
│ • Node metrics (CPU, Mem)  │
│ • PostgreSQL metrics       │
│ • Redis metrics            │
│ • Application metrics      │
├────────────────────────────┤
│ Storage: prometheus_data   │ (30 days retention)
└────────┬───────────────────┘
         │
    ┌────▼──────────────────┐
    │  Grafana (3000)       │ ← Dashboards & Alerts
    ├───────────────────────┤
    │ • System health       │
    │ • Database health     │
    │ • Application health  │
    │ • Business metrics    │
    └───────────────────────┘
```

**Key Dashboards to Create:**
1. System Overview (CPU, Memory, Disk, Network)
2. Database Performance (Queries, Connections, Cache Hit)
3. Application Health (Uptime, Response Time, Error Rate)
4. Redis Status (Memory, Hit Rate, Keys)
5. Container Status (All services running state)

---

## ✅ Configuration Checklist

- [x] Docker resource limits applied
- [x] PostgreSQL optimization parameters
- [x] Redis configuration optimized
- [x] RabbitMQ tuning settings
- [x] Gunicorn worker configuration
- [x] Health checks improved
- [x] Logging configured
- [ ] OS-level networking tuning (next step)
- [ ] File descriptor limits (next step)
- [ ] Monitoring dashboards (next step)
- [ ] Backup automation (next step)
- [ ] Alert configuration (next step)

---

## 📚 Related Documentation

- **OPTIMIZATION_PLAN.md** - Detailed optimization guide
- **DEPLOYMENT_CHECKLIST.md** - Step-by-step deployment
- **QUICK_REFERENCE.md** - Quick troubleshooting guide
- **Memory Notes** - `/memories/repo/production-optimization.md`

