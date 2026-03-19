# Data Pipeline Microservice - Simplified Architecture

**Status**: Backend data collection and prediction engine for GrainTrade  
**Version**: 0.2.0-simplified  
**Principle**: KISS (Keep It Simple, Stupid)

---

## What It Does

- Collects grain commodity price data from 6 Ukrainian sources
- Stores data in Delta Lake (bronze/silver/gold layers)
- Predicts prices using historical trends
- Publishes predictions to frontend API and Telegram channel
- Handles Telegram bot input for manual data posting

## Quick Start

### 1. Setup

```bash
cd data-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials
```

### 2. Configure Data Sources

Edit `.env` - each parser has its own section:

```bash
# Yahoo Finance
YF_TICKERS=CBOT_ZWZ21,CBOT_ZWH22,CBOT_ZYH22
YF_PERIOD=1y
YF_INTERVAL=daily

# Investing.com
IC_INSTRUMENTS=WHEAT,CORN,SOY
IC_START_DATE=2023-01-01

# APK Inform
APK_REGIONS=Kyiv,Kharkiv,Odesa
APK_UPLOAD_STORAGE=true
```

### 3. Run Data Pipeline

Start the service:
```bash
fastapi run app/main.py
```

API available at `http://localhost:8004/docs`

## Available Parsers

All parsers store data in Bronze layer (raw), then transform to Silver (clean).

| Parser | Source | Env Vars | Frequency |
|--------|--------|----------|-----------|
| `apk_inform` | APK-Inform.com | `APK_*` | Daily |
| `investing_com` | Investing.com | `IC_*` | Daily |
| `yfinance` | Yahoo Finance | `YF_*` | Hourly |
| `tripoli_land` | Tripoli.land | `TL_*` | Daily |
| `currency` | Exchange rates | `CURR_*` | Hourly |
| `graintradecomua` | GrainTrade.com.ua | `GT_*` | Daily |

## Running Ingestion Jobs

### Start a job via API

```bash
# Start data collection from Yahoo Finance
curl -X POST http://localhost:8004/ingestion/start/yfinance

# Response:
{
  "job_id": "job_abc123",
  "parser_name": "yfinance",
  "status": "started"
}
```

### Check job status

```bash
curl http://localhost:8004/ingestion/jobs/job_abc123

# Response:
{
  "job_id": "job_abc123",
  "parser_name": "yfinance",
  "status": "completed",
  "records_read": 150,
  "records_written": 145,
  "completed_at": "2026-01-13T10:45:00"
}
```

### List all parsers

```bash
curl http://localhost:8004/ingestion/parsers

# Shows available parsers and their current configuration
```

## Data Flow

```
Parser (get data)
    ↓
Bronze Layer (raw data storage in Delta Lake)
    ↓
Silver Layer (cleaning, deduplication)
    ↓
Gold Layer (aggregates, predictions)
    ↓
Telegram Channel (publish predictions)
Forecast API (frontend queries)
```

## Adding a New Parser

1. Create file: `app/parsers/my_parser.py`

```python
from app.parsers.base_parser import BaseParser

class MyParser(BaseParser):
    def __init__(self, config_param1, config_param2):
        self.config_param1 = config_param1
        self.config_param2 = config_param2
    
    def parse(self):
        # Your data collection logic
        # Return list of dictionaries or pandas DataFrame
        return [{"date": "2026-01-13", "price": 350}]
```

2. Add to `app/services/ingestion_service.py`:

```python
from app.parsers import MyParser

if parser_name == "my_parser":
    return MyParser(
        config_param1=settings.MY_PARAM1,
        config_param2=settings.MY_PARAM2,
    )
```

3. Add to `.env`:

```bash
MY_PARAM1=value1
MY_PARAM2=value2
```

4. Test:

```bash
curl -X POST http://localhost:8004/ingestion/start/my_parser
```

That's it!

## Modifying Parser Configuration

Want to change which tickers Yahoo Finance fetches? Just edit `.env`:

```bash
# Old
YF_TICKERS=CBOT_ZWZ21,CBOT_ZWH22

# New
YF_TICKERS=CBOT_ZWZ21,CBOT_ZWH22,CBOT_ZYH22
```

Restart the service, next ingestion will use new config. No database changes needed.

## Database Models

### IngestionLog

Tracks every data collection job:
```python
IngestionLog(
    job_id="job_abc123",
    parser_name="yfinance",
    status="completed",  # started, running, completed, failed
    records_read=150,
    records_written=145,
    error_message=None,
    started_at="2026-01-13T10:00:00",
    completed_at="2026-01-13T10:45:00",
)
```

Use this to debug failures and monitor system health.

### Commodity

Price data stored in Delta Lake tables:
```
/delta/bronze/{parser_name}_{timestamp}/
/delta/silver/{parser_name}_clean/
/delta/gold/predictions_{category}/
```

## Monitoring

### Check recent jobs

```bash
# Last 10 jobs
curl "http://localhost:8004/ingestion/jobs?limit=10"

# Failed jobs only
curl "http://localhost:8004/ingestion/jobs?status=failed"

# Jobs from specific parser
curl "http://localhost:8004/ingestion/jobs?parser_name=yfinance"
```

### Check logs

```bash
# From running service
tail -f logs/data_pipeline.log

# Check for errors
grep ERROR logs/data_pipeline.log

# Check specific parser
grep yfinance logs/data_pipeline.log
```

### Health check

```bash
curl http://localhost:8004/health

# Response:
{
  "status": "healthy",
  "database": "connected",
  "spark": "running"
}
```

## Troubleshooting

### Job status is "failed"

1. Check error message:
```bash
curl http://localhost:8004/ingestion/jobs/job_abc123 | jq .error_message
```

2. Check logs:
```bash
grep "job_abc123" logs/data_pipeline.log
```

### Records not appearing

1. Check parser configuration in `.env`
2. Check if parser is active: `curl http://localhost:8004/ingestion/parsers`
3. Run a test job and check logs

### Memory issues with Spark

Adjust in `.env`:
```bash
SPARK_MASTER=local[2]  # Use 2 cores instead of all
```

### Telegram not publishing

Check configuration:
```bash
TELEGRAM_ENABLED=true
TELEGRAM_TOKEN=your_token
TELEGRAM_CHANNEL_ID=your_channel_id
```

## Architecture Decisions

**Why not use factory pattern?** - We have 6 fixed parsers, not a plugin system. Direct code is simpler.

**Why not validate configs in a separate layer?** - Configuration comes from .env which Python validates at import time. Parser errors are caught and logged.

**Why Delta Lake?** - Handles schema evolution, ACID transactions, time travel (check historical data).

**Why Spark?** - Can process larger datasets, supports distributed computing if needed later.

## Contributing

- Add new parser: Create `app/parsers/your_parser.py`
- Add new prediction model: Create `app/models/your_model.py`
- Modify existing parser: Edit the .py file directly, update .env
- New feature: Add to appropriate router, add tests

## Deployment

### Development
```bash
fastapi dev app/main.py
```

### Production
```bash
# Build Docker image
docker build -t graintrade-pipeline .

# Run with environment file
docker run --env-file .env graintrade-pipeline
```

See `Dockerfile` for details.

## Files Structure

```
app/
├── main.py              # FastAPI app
├── config.py            # Settings from .env
├── database.py          # Database connection
├── logger.py            # Logging configuration
│
├── models/              # SQLAlchemy models
│   ├── commodity_model.py
│   ├── ingestion_log_model.py
│   └── prediction_model.py
│
├── parsers/             # Data collectors
│   ├── apk_inform.py
│   ├── investing_com.py
│   ├── yfinance.py
│   ├── tripoli_land.py
│   ├── currency.py
│   └── graintradecomua.py
│
├── routers/             # API endpoints
│   ├── ingestion_router.py     # Start/monitor jobs
│   ├── commodity_router.py     # Query prices
│   ├── forecast_router.py      # Get predictions
│   └── health_router.py        # Health check
│
├── services/
│   └── ingestion_service.py    # Orchestration
│
└── spark_services/      # Data processing
    └── (Delta Lake operations)

requirements.txt         # Python dependencies
.env.example            # Configuration template
Dockerfile              # Container definition
README.md              # This file
```

## Performance

- Typical ingestion job: 30 seconds - 2 minutes (depends on data source)
- Storage: ~100MB per day across all parsers
- Predictions: Generated daily at 6 AM UTC

## Support

Issues or questions? Check:
1. Logs: `grep ERROR logs/data_pipeline.log`
2. Job status API: `/ingestion/jobs/{job_id}`
3. Configuration: Review `.env` matches your sources

---

**Last updated**: 2026-01-13  
**Maintainer**: GrainTrade team
