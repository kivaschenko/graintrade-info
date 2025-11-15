#!/bin/bash

# Create a working dashboard with available metrics

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
USERNAME="${GRAFANA_USERNAME:-admin}"
PASSWORD="${GRAFANA_PASSWORD:-changeme}"

echo "🚀 Creating Working GrainTrade Monitoring Dashboard..."

# Delete old dashboards first
curl -X DELETE -u "$USERNAME:$PASSWORD" "$GRAFANA_URL/api/dashboards/uid/a628fbfc-4ae3-44f8-bd05-4999be40b374"
curl -X DELETE -u "$USERNAME:$PASSWORD" "$GRAFANA_URL/api/dashboards/uid/1784082c-66fb-4472-9b20-402efb1f5865"

# Create new working dashboard
curl -X POST \
  -H "Content-Type: application/json" \
  -u "$USERNAME:$PASSWORD" \
  "$GRAFANA_URL/api/dashboards/db" \
  -d '{
    "dashboard": {
      "id": null,
      "title": "GrainTrade Service Monitoring",
      "tags": ["graintrade", "services"],
      "timezone": "browser",
      "panels": [
        {
          "id": 1,
          "title": "Service Status",
          "type": "stat",
          "targets": [
            {
              "expr": "up",
              "refId": "A",
              "legendFormat": "{{job}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "mappings": [
                {"options": {"0": {"text": "DOWN", "color": "red"}}, "type": "value"},
                {"options": {"1": {"text": "UP", "color": "green"}}, "type": "value"}
              ],
              "noValue": "No Data"
            }
          },
          "gridPos": {"h": 8, "w": 24, "x": 0, "y": 0}
        },
        {
          "id": 2,
          "title": "Scrape Duration",
          "type": "timeseries",
          "targets": [
            {
              "expr": "scrape_duration_seconds",
              "refId": "A",
              "legendFormat": "{{job}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "s"
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
        },
        {
          "id": 3,
          "title": "Samples Scraped",
          "type": "timeseries",
          "targets": [
            {
              "expr": "scrape_samples_scraped",
              "refId": "A",
              "legendFormat": "{{job}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "short"
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
        }
      ],
      "time": {
        "from": "now-30m",
        "to": "now"
      },
      "refresh": "10s"
    },
    "overwrite": true
  }'

echo -e "\n✅ Working Dashboard created! Visit: $GRAFANA_URL/dashboards"