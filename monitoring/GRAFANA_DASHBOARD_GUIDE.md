# GrainTrade Grafana Dashboard Setup Guide

## 📊 Dashboard Creation Guide

### 1. System Monitoring Dashboard

#### Panel 1: CPU Usage
- **Type**: Stat
- **Query**: `100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- **Unit**: Percent
- **Thresholds**: Green < 70%, Yellow 70-90%, Red > 90%

#### Panel 2: Memory Usage  
- **Type**: Stat
- **Query**: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
- **Unit**: Percent
- **Thresholds**: Green < 70%, Yellow 70-90%, Red > 90%

#### Panel 3: Disk Usage
- **Type**: Stat
- **Query**: `(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100`
- **Unit**: Percent
- **Thresholds**: Green < 70%, Yellow 70-90%, Red > 90%

#### Panel 4: Service Uptime
- **Type**: Stat
- **Query**: `up`
- **Transform**: Group by job
- **Value Mappings**: 0 = DOWN (Red), 1 = UP (Green)

### 2. Application Performance Dashboard

#### Panel 1: HTTP Request Rate
- **Type**: Time Series
- **Query**: `rate(http_requests_total[5m])`
- **Legend**: `{{job}} - {{method}} {{status}}`
- **Unit**: Requests per second

#### Panel 2: Response Time Percentiles
- **Type**: Time Series
- **Queries**:
  - `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` (95th percentile)
  - `histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))` (50th percentile)
- **Unit**: Seconds

#### Panel 3: Error Rate
- **Type**: Time Series
- **Query**: `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])`
- **Unit**: Percent

### 3. Database Monitoring Dashboard

#### Panel 1: PostgreSQL Connections
- **Type**: Time Series
- **Queries**:
  - `pg_stat_activity_count` (Active connections)
  - `pg_settings_max_connections` (Max connections)

#### Panel 2: Query Performance
- **Type**: Time Series
- **Query**: `rate(pg_stat_statements_calls[5m])`
- **Legend**: SQL queries per second

#### Panel 3: Database Size
- **Type**: Stat
- **Query**: `pg_database_size_bytes`
- **Unit**: Bytes

### 4. Container Monitoring Dashboard

#### Panel 1: Container CPU Usage
- **Type**: Time Series
- **Query**: `rate(container_cpu_usage_seconds_total{name=~".+"}[5m]) * 100`
- **Unit**: Percent

#### Panel 2: Container Memory Usage
- **Type**: Time Series
- **Query**: `container_memory_usage_bytes{name=~".+"}`
- **Unit**: Bytes

#### Panel 3: Network I/O
- **Type**: Time Series
- **Queries**:
  - `rate(container_network_receive_bytes_total[5m])` (Inbound)
  - `rate(container_network_transmit_bytes_total[5m])` (Outbound)
- **Unit**: Bytes per second

## 🔧 Quick Setup Instructions

### Method 1: Import Dashboard JSONs
1. Go to Grafana → **Dashboards** → **Import**
2. Copy and paste the JSON from the dashboard files
3. Click **Load** and **Import**

### Method 2: Manual Creation
1. Go to Grafana → **Dashboards** → **New Dashboard**
2. Click **Add Panel**
3. Enter the queries and configure as described above
4. Save the dashboard

## 🎯 Essential Queries for GrainTrade

### System Health
```promql
# CPU Usage
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory Usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk Usage
(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100

# Load Average
node_load1

# Network Traffic
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])
```

### Application Metrics
```promql
# Service Uptime
up{job=~"backend|frontend|chat|notifications|landing"}

# HTTP Requests
rate(http_requests_total[5m])

# Response Time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error Rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

### Database Metrics
```promql
# PostgreSQL Connections
pg_stat_activity_count
pg_settings_max_connections

# Query Rate
rate(pg_stat_statements_calls[5m])

# Database Size
pg_database_size_bytes

# Cache Hit Ratio
pg_stat_database_blks_hit / (pg_stat_database_blks_read + pg_stat_database_blks_hit)
```

### Container Metrics
```promql
# Container CPU
rate(container_cpu_usage_seconds_total{name=~".+"}[5m]) * 100

# Container Memory
container_memory_usage_bytes{name=~".+"}

# Container Network
rate(container_network_receive_bytes_total[5m])
rate(container_network_transmit_bytes_total[5m])
```

## 🚨 Alerting Rules

### Critical Alerts
- CPU > 90% for 5 minutes
- Memory > 95% for 5 minutes  
- Disk > 85% for 1 minute
- Service down for 1 minute

### Warning Alerts
- CPU > 70% for 10 minutes
- Memory > 80% for 10 minutes
- Disk > 70% for 5 minutes
- Error rate > 5% for 5 minutes

## 📱 Dashboard Variables

Add these variables to make dashboards dynamic:

### Instance Variable
- **Name**: `instance`
- **Type**: Query
- **Query**: `label_values(up, instance)`

### Job Variable  
- **Name**: `job`
- **Type**: Query
- **Query**: `label_values(up, job)`

### Time Range Variable
- **Name**: `interval`
- **Type**: Interval
- **Values**: `1m,5m,10m,30m,1h`

## 🎨 Dashboard Best Practices

1. **Use consistent time ranges** across panels
2. **Set appropriate refresh intervals** (30s for real-time, 5m for historical)
3. **Add meaningful legends** using `{{label}}` syntax
4. **Use appropriate visualizations** (Stats for current values, Time Series for trends)
5. **Set sensible thresholds** with color coding
6. **Group related panels** logically
7. **Add panel descriptions** for complex queries
8. **Use template variables** for flexibility

## 🔄 Refresh and Update

- Set dashboard refresh to **30 seconds** for live monitoring
- Use **relative time ranges** (last 1h, last 24h) instead of absolute
- Enable **auto-refresh** for operational dashboards
- Set up **playlist mode** for display screens