# Monitoring Setup

This document describes the integrated monitoring services in the main docker-compose.yaml file.

## Services Added

### 🧩 Node Exporter
- **Purpose**: Collects host metrics (CPU, memory, disk, network)
- **Port**: Uses host network mode
- **Endpoint**: `http://localhost:9100/metrics`

### 📊 PostgreSQL Exporter
- **Purpose**: Monitors PostgreSQL database performance
- **Port**: 9187
- **Configuration**: Update `DATA_SOURCE_NAME` environment variable with your production PostgreSQL credentials

### 🔴 Redis Exporter
- **Purpose**: Monitors Redis performance and metrics
- **Port**: 9121
- **Configuration**: Update `--redis.addr` parameter with your production Redis connection string

### 📈 Prometheus
- **Purpose**: Metrics collection and storage
- **Port**: 9090
- **Web UI**: `http://localhost:9090`
- **Configuration**: Uses `./monitoring/prometheus.yml`

### 🧠 Grafana
- **Purpose**: Metrics visualization and dashboards
- **Port**: 3000
- **Web UI**: `http://localhost:3000`
- **Default credentials**: admin/admin123

## Setup Instructions

1. **Update Database Connection**: 
   - Modify the `DATA_SOURCE_NAME` in the `postgres_exporter` service to match your production PostgreSQL credentials
   
2. **Update Redis Connection**:
   - Modify the `--redis.addr` parameter in the `redis_exporter` service to match your production Redis instance

3. **Start Monitoring Services**:
   ```bash
   docker-compose up -d node_exporter postgres_exporter redis_exporter prometheus grafana
   ```

4. **Access Grafana**:
   - Navigate to `http://localhost:3000`
   - Login with admin/admin123
   - Add Prometheus as a data source: `http://prometheus:9090`
   - Import or create dashboards for your metrics

## Security Notes

- Change default Grafana credentials in production
- Consider using environment variables for sensitive database connection strings
- Ensure firewall rules allow access only to necessary ports

## Ports Used

- 3000: Grafana
- 9090: Prometheus
- 9187: PostgreSQL Exporter
- 9121: Redis Exporter
- Node Exporter uses host network mode

## Volumes

- `prometheus_data`: Stores Prometheus metrics data
- `grafana_data`: Stores Grafana dashboards and configuration