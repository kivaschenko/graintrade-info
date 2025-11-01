#!/bin/bash

# Create Application Monitoring Dashboard

GRAFANA_URL="http://65.108.68.57:3000"
USERNAME="civaschenko"
PASSWORD="Teodorathome11"

echo "🚀 Creating GrainTrade Application Monitoring Dashboard..."

# Create Application Dashboard
curl -X POST \
  -H "Content-Type: application/json" \
  -u "$USERNAME:$PASSWORD" \
  "$GRAFANA_URL/api/dashboards/db" \
  -d '{
    "dashboard": {
      "id": null,
      "title": "GrainTrade Application Monitoring",
      "tags": ["graintrade", "applications"],
      "timezone": "browser",
      "panels": [
        {
          "id": 1,
          "title": "Disk Usage",
          "type": "stat",
          "targets": [
            {
              "expr": "(1 - (node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"})) * 100",
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
                  {"color": "red", "value": 85}
                ]
              }
            }
          },
          "gridPos": {"h": 6, "w": 8, "x": 0, "y": 0}
        },
        {
          "id": 2,
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
          "gridPos": {"h": 6, "w": 8, "x": 8, "y": 0}
        },
        {
          "id": 3,
          "title": "Network Traffic",
          "type": "timeseries",
          "targets": [
            {
              "expr": "rate(node_network_receive_bytes_total{device!=\"lo\"}[5m])",
              "refId": "A",
              "legendFormat": "Inbound {{device}}"
            },
            {
              "expr": "rate(node_network_transmit_bytes_total{device!=\"lo\"}[5m])",
              "refId": "B",
              "legendFormat": "Outbound {{device}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "Bps"
            }
          },
          "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0}
        },
        {
          "id": 4,
          "title": "CPU Usage Over Time",
          "type": "timeseries",
          "targets": [
            {
              "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
              "refId": "A",
              "legendFormat": "CPU Usage %"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "percent",
              "min": 0,
              "max": 100
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
        },
        {
          "id": 5,
          "title": "Memory Usage Over Time",
          "type": "timeseries",
          "targets": [
            {
              "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
              "refId": "A",
              "legendFormat": "Memory Usage %"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "percent",
              "min": 0,
              "max": 100
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
        }
      ],
      "time": {
        "from": "now-1h",
        "to": "now"
      },
      "refresh": "30s"
    },
    "overwrite": false
  }'

echo -e "\n✅ Application Dashboard created! Visit: $GRAFANA_URL/dashboards"