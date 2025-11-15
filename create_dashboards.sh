#!/bin/bash

# Quick script to import dashboards via Grafana API

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
USERNAME="${GRAFANA_USERNAME:-admin}"
PASSWORD="${GRAFANA_PASSWORD:-changeme}"

echo "🚀 Creating GrainTrade System Overview Dashboard..."

# Create System Overview Dashboard
curl -X POST \
  -H "Content-Type: application/json" \
  -u "$USERNAME:$PASSWORD" \
  "$GRAFANA_URL/api/dashboards/db" \
  -d '{
    "dashboard": {
      "id": null,
      "title": "GrainTrade System Overview",
      "tags": ["graintrade", "infrastructure"],
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
              }
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
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
              }
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
        },
        {
          "id": 3,
          "title": "Service Status",
          "type": "stat",
          "targets": [
            {
              "expr": "up",
              "refId": "A"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "mappings": [
                {"options": {"0": {"text": "DOWN", "color": "red"}}, "type": "value"},
                {"options": {"1": {"text": "UP", "color": "green"}}, "type": "value"}
              ]
            }
          },
          "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
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

echo -e "\n✅ Dashboard created! Visit: $GRAFANA_URL/dashboards"