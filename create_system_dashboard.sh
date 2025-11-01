#!/bin/bash

# Create a dashboard with real system metrics

GRAFANA_URL="http://65.108.68.57:3000"
USERNAME="civaschenko"
PASSWORD="Teodorathome11"

echo "🚀 Creating Real System Metrics Dashboard..."

# Create dashboard with working system metrics
curl -X POST \
  -H "Content-Type: application/json" \
  -u "$USERNAME:$PASSWORD" \
  "$GRAFANA_URL/api/dashboards/db" \
  -d '{
    "dashboard": {
      "id": null,
      "title": "GrainTrade System Metrics",
      "tags": ["graintrade", "system"],
      "timezone": "browser",
      "panels": [
        {
          "id": 1,
          "title": "CPU Usage",
          "type": "stat",
          "targets": [
            {
              "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
              "refId": "A"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "percent",
              "thresholds": {
                "steps": [
                  {"color": "green", "value": null},
                  {"color": "yellow", "value": 70},
                  {"color": "red", "value": 90}
                ]
              },
              "min": 0,
              "max": 100
            }
          },
          "gridPos": {"h": 6, "w": 8, "x": 0, "y": 0}
        },
        {
          "id": 2,
          "title": "Memory Usage",
          "type": "stat",
          "targets": [
            {
              "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
              "refId": "A"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "percent",
              "thresholds": {
                "steps": [
                  {"color": "green", "value": null},
                  {"color": "yellow", "value": 70},
                  {"color": "red", "value": 90}
                ]
              },
              "min": 0,
              "max": 100
            }
          },
          "gridPos": {"h": 6, "w": 8, "x": 8, "y": 0}
        },
        {
          "id": 3,
          "title": "Load Average",
          "type": "stat",
          "targets": [
            {
              "expr": "node_load1",
              "refId": "A"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "short",
              "thresholds": {
                "steps": [
                  {"color": "green", "value": null},
                  {"color": "yellow", "value": 2},
                  {"color": "red", "value": 4}
                ]
              }
            }
          },
          "gridPos": {"h": 6, "w": 8, "x": 16, "y": 0}
        },
        {
          "id": 4,
          "title": "CPU Usage Over Time",
          "type": "timeseries",
          "targets": [
            {
              "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
              "refId": "A",
              "legendFormat": "CPU %"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "percent",
              "min": 0,
              "max": 100,
              "custom": {
                "drawStyle": "line",
                "fillOpacity": 10
              }
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 6}
        },
        {
          "id": 5,
          "title": "Memory Usage Over Time",
          "type": "timeseries",
          "targets": [
            {
              "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
              "refId": "A",
              "legendFormat": "Memory %"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "percent",
              "min": 0,
              "max": 100,
              "custom": {
                "drawStyle": "line",
                "fillOpacity": 10
              }
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 6}
        }
      ],
      "time": {
        "from": "now-30m",
        "to": "now"
      },
      "refresh": "10s"
    },
    "overwrite": false
  }'

echo -e "\n✅ System Metrics Dashboard created! Visit: $GRAFANA_URL/dashboards"