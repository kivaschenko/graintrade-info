# Quick Start Guide - Data Pipeline

## 🚀 Running the Pipeline

### Manual Execution
```bash
cd /home/ikost/Projects/graintrade-info/data-pipeline
source venv/bin/activate
python -m app.services.grain_forecast_pipeline
```

### With Test Script
```bash
chmod +x test_pipeline.sh
./test_pipeline.sh
```

## 📊 Checking Results

### View Latest Predictions
```sql
psql -U data_analytic -d analytic_db -c \
  "SELECT commodity_name, region, predicted_price, prediction_date, confidence_score 
   FROM predictions 
   ORDER BY created_at DESC 
   LIMIT 20;"
```

### View Latest Commodities
```sql
psql -U data_analytic -d analytic_db -c \
  "SELECT name, region, price, currency, date 
   FROM commodities 
   WHERE source_name = 'Yahoo Finance Predictive Pipeline' 
   ORDER BY updated_at DESC 
   LIMIT 10;"
```

### Check Artifacts
```bash
# List parquet files
ls -lh parsers_results/grain_forecast/

# View parquet content with pandas
python -c "import pandas as pd; df = pd.read_parquet('parsers_results/grain_forecast/silver_*.parquet'); print(df.head())"
```

### Check RabbitMQ
```bash
# List queues and message counts
rabbitmqctl list_queues name messages

# Peek at messages (without consuming)
rabbitmqadmin get queue=predictions_queue count=5
```

## 🌐 API Testing

### Start API Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

### Test Endpoints

#### Health Check
```bash
curl http://localhost:8004/health
```

#### Get Homepage Forecasts
```bash
curl http://localhost:8004/forecasts/homepage | jq
```

#### Get All Forecasts
```bash
curl "http://localhost:8004/forecasts/?days_ahead=7&limit=50" | jq
```

#### Get Specific Commodity
```bash
curl "http://localhost:8004/forecasts/Wheat%20Futures?days_ahead=7" | jq
```

## 🐛 Debugging

### Check Logs
```bash
# Application logs
tail -f logs/data_pipeline.log

# Python errors
python -m app.services.grain_forecast_pipeline 2>&1 | grep -i error
```

### Common Issues

#### 1. Database Connection Error
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection
psql -U data_analytic -d analytic_db -c "SELECT 1;"
```

#### 2. RabbitMQ Connection Error
```bash
# Check RabbitMQ is running
systemctl status rabbitmq-server

# Check credentials in .env
cat .env | grep RABBITMQ
```

#### 3. Yahoo Finance Download Fails
- Check internet connection
- Yahoo Finance may be rate-limiting - add delays
- Try alternative data source (Investing.com)

#### 4. Delta Lake Errors
- Known issue with Spark 4.1 + Delta Lake compatibility
- Workaround: Parquet files still created successfully
- Fix: Downgrade to Spark 3.5.x (see AUDIT_AND_ROADMAP.md)

## 📝 Configuration

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql://data_analytic:password@localhost:5432/analytic_db

# Delta Lake Paths
BRONZE_LAYER_PATH=/data/delta/bronze
SILVER_LAYER_PATH=/data/delta/silver
GOLD_LAYER_PATH=/data/delta/gold

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
RABBITMQ_VHOST=/

# Hetzner Storage (optional)
HETZNER_STORAGE_ENDPOINT=hel1.your-objectstorage.com
HETZNER_STORAGE_ACCESS_KEY=your_access_key
HETZNER_STORAGE_SECRET_KEY=your_secret_key
HETZNER_STORAGE_BUCKET=graintrade-info

# API
API_HOST=0.0.0.0
API_PORT=8004
```

## 🔄 Scheduled Runs

### Cron (Simple)
```bash
# Edit crontab
crontab -e

# Add daily run at 6 AM
0 6 * * * cd /home/ikost/Projects/graintrade-info/data-pipeline && source venv/bin/activate && python -m app.services.grain_forecast_pipeline >> logs/cron.log 2>&1
```

### Systemd Timer (Better)
```bash
# Create service file
sudo nano /etc/systemd/system/grain-forecast.service

[Unit]
Description=Grain Forecast Pipeline
After=network.target postgresql.service rabbitmq-server.service

[Service]
Type=oneshot
User=ikost
WorkingDirectory=/home/ikost/Projects/graintrade-info/data-pipeline
ExecStart=/home/ikost/Projects/graintrade-info/data-pipeline/venv/bin/python -m app.services.grain_forecast_pipeline
StandardOutput=journal
StandardError=journal

# Create timer file
sudo nano /etc/systemd/system/grain-forecast.timer

[Unit]
Description=Run Grain Forecast Pipeline Daily
Requires=grain-forecast.service

[Timer]
OnCalendar=daily
OnCalendar=06:00
Persistent=true

[Install]
WantedBy=timers.target

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable grain-forecast.timer
sudo systemctl start grain-forecast.timer

# Check status
sudo systemctl status grain-forecast.timer
```

## 🔍 Monitoring

### Pipeline Metrics
```python
# Add to pipeline code
summary = pipeline.run()
print(json.dumps(summary, indent=2))
```

Output:
```json
{
  "status": "completed",
  "records_ingested": 847,
  "records_transformed": 847,
  "commodities_updated": 3,
  "predictions_saved": 49,
  "predictions_published": 49,
  "usd_uah_rate": 43.2,
  "bronze_artifact": "/path/to/bronze_20260109.parquet",
  "silver_artifact": "/path/to/silver_20260109.parquet"
}
```

### Grafana Dashboard (Future)
- Track pipeline execution time
- Monitor prediction accuracy
- Alert on failures
- Visualize commodity price trends

## 📚 Next Steps

1. **Test the Fix**: Run `./test_pipeline.sh` and verify no errors
2. **Test API**: Start server and curl `/forecasts/homepage`
3. **Check Frontend**: Integrate forecast widget in Vue.js
4. **Monitor**: Watch logs and database for 24 hours
5. **Schedule**: Set up cron/timer for daily runs

## 🆘 Support

**Issues**: Check [AUDIT_AND_ROADMAP.md](./AUDIT_AND_ROADMAP.md)  
**Contact**: civaschenko@yahoo.com  
**Logs**: `logs/data_pipeline.log`
