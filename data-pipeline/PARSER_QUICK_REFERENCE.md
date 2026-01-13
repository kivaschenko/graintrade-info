# Parser Configuration - Quick Reference

## TL;DR - 3 Steps

### 1. Save Config to DataSource
```python
config = {
    "parser_type": "apk_inform",
    "regions": ["Odesa", "Mykolaiv"]
}

data_source = DataSource(
    name="APK-Inform",
    config=config  # ← Store as JSON
)
```

### 2. Use Factory in Pipeline
```python
parser = ParserFactory.create_parser(data_source)
df = parser.parse()
```

### 3. Ingestion Endpoint
```bash
curl -X POST "/ingestion/start" \
  -d '{"data_source_id": 1, "layer": "bronze"}'
```

---

## Config Structure by Parser

| Parser | Key Config | Example |
|--------|-----------|---------|
| **apk_inform** | `regions: list` | `{"parser_type": "apk_inform", "regions": ["Odesa"]}` |
| **investing_com** | `instruments: list` | `{"parser_type": "investing_com", "instruments": [{"symbol": "ZWZ"}]}` |
| **yfinance** | `tickers: list` | `{"parser_type": "yfinance", "tickers": ["ZWZ=F"]}` |
| **tripoli_land** | `companies: list` | `{"parser_type": "tripoli_land", "companies": ["nibulon"]}` |
| **currency** | (none) | `{"parser_type": "currency"}` |

---

## API Quick Calls

### Register Data Source
```bash
curl -X POST "http://localhost:8001/data-sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Parser",
    "source_type": "web_scraping",
    "config": {
      "parser_type": "apk_inform",
      "regions": ["Odesa"]
    }
  }'
```

### Start Ingestion Job
```bash
curl -X POST "http://localhost:8001/ingestion/start" \
  -H "Content-Type: application/json" \
  -d '{"data_source_id": 1, "layer": "bronze"}'
```

### Check Job Status
```bash
curl -X GET "http://localhost:8001/ingestion/jobs/job_abc123"
```

### Update Config
```bash
curl -X PATCH "http://localhost:8001/data-sources/1" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "parser_type": "apk_inform",
      "regions": ["Odesa", "Mykolaiv", "Kherson"]
    }
  }'
```

### Get Supported Parsers
```bash
curl -X GET "http://localhost:8001/ingestion/parsers"
```

---

## Python Usage

### Create Parser from DataSource
```python
from app.services.parser_factory import ParserFactory
from app.models import DataSource

data_source = db.query(DataSource).filter_by(id=1).first()
parser = ParserFactory.create_parser(data_source)
df = parser.parse()
```

### Validate Config
```python
from app.services.config_validator import ConfigValidator

is_valid, errors = ConfigValidator.validate(data_source.config)
if is_valid:
    # proceed
else:
    print(f"Config errors: {errors}")
```

### Create DataSource Programmatically
```python
from app.models import DataSource

ds = DataSource(
    name="My Parser",
    source_type="web_scraping",
    config={
        "parser_type": "apk_inform",
        "regions": ["Odesa"]
    }
)
db.add(ds)
db.commit()
```

---

## Error Handling

```python
try:
    parser = ParserFactory.create_parser(data_source)
    df = parser.parse()
except ValueError as e:
    # Config validation errors
    logger.error(f"Invalid config: {e}")
except RuntimeError as e:
    # Parser instantiation errors
    logger.error(f"Parser creation failed: {e}")
except Exception as e:
    # Parser execution errors
    logger.error(f"Parser execution failed: {e}")
```

---

## Common Configurations

### APK-Inform - All Regions
```json
{
  "parser_type": "apk_inform",
  "regions": ["Odesa", "Mykolaiv", "Kherson", "Zaporizhzhia"]
}
```

### YFinance - Multiple Commodities
```json
{
  "parser_type": "yfinance",
  "tickers": ["ZWZ=F", "ZCZ=F", "SOYB=F"],
  "period": "2y"
}
```

### Investing.com - Futures
```json
{
  "parser_type": "investing_com",
  "instruments": [
    {"symbol": "ZWZ", "name": "Wheat CBOT"},
    {"symbol": "ZCZ", "name": "Corn CBOT"}
  ],
  "start_date": "2023-01-01",
  "end_date": "2024-01-12"
}
```

### Tripoli Land - Selected Companies
```json
{
  "parser_type": "tripoli_land",
  "companies": ["nibulon", "kernel", "lnz-group"]
}
```

---

## Database Schema

```sql
-- Data Source stores config as JSON
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    source_type VARCHAR(50),
    config JSONB,  -- Stores parser parameters
    is_active BOOLEAN DEFAULT TRUE,
    last_ingestion TIMESTAMP,
    ...
);

-- Ingestion Log tracks execution
CREATE TABLE ingestion_logs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50),
    data_source_id INTEGER,
    status VARCHAR(20),  -- started, running, completed, failed
    records_read INTEGER,
    records_written INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    ...
);
```

---

## File Locations

| File | Purpose |
|------|---------|
| `app/models/data_source_model.py` | DataSource with config column |
| `app/services/parser_factory.py` | Create parsers from config |
| `app/services/config_validator.py` | Validate configs |
| `app/routers/ingestion_router_enhanced.py` | Enhanced ingestion API |
| `PARSER_CONFIG_GUIDE.md` | Full documentation |
| `PARSER_USAGE_EXAMPLES.md` | Practical examples |
| `PARSER_IMPLEMENTATION_GUIDE.md` | Implementation details |

---

## Debugging

### Enable Debug Logging
```python
# app/config.py
LOG_LEVEL = "DEBUG"
```

### Check DataSource Config
```sql
SELECT id, name, config FROM data_sources WHERE id = 1;
```

### Check Ingestion Logs
```sql
SELECT * FROM ingestion_logs 
WHERE data_source_id = 1 
ORDER BY started_at DESC 
LIMIT 10;
```

### Test Parser Creation
```python
from app.services.parser_factory import ParserFactory

try:
    parser = ParserFactory.create_parser(data_source)
    print(f"✓ Parser created: {type(parser).__name__}")
except Exception as e:
    print(f"✗ Error: {e}")
```

---

## Key Points

✅ **Always use `config` field** - Store parser parameters as JSON in DataSource.config

✅ **Use ParserFactory** - Never instantiate parsers directly in pipeline logic

✅ **Validate first** - Call ConfigValidator before creating parser

✅ **Check IngestionLog** - All jobs are tracked with full details

✅ **Handle errors gracefully** - Catch and log all exceptions

✅ **Use appropriate parser_type** - Must match registered parsers

✅ **Document your config** - Comment on required and optional fields

---

## Flow Diagram

```
User Request
    │
    ├─→ Register DataSource with config
    │
    ├─→ Trigger Ingestion (/ingestion/start)
    │
    ├─→ Validate Config (ConfigValidator)
    │
    ├─→ Create Parser (ParserFactory)
    │
    ├─→ Execute Parser (parser.parse())
    │
    ├─→ Store Results (Bronze Layer)
    │
    ├─→ Update IngestionLog
    │
    └─→ Return Status (job_id, status)
        │
        └─→ Check Status (/ingestion/jobs/{job_id})
```

---

## Example Workflow

```bash
# 1. Register
curl -X POST "http://localhost:8001/data-sources" -d '{
  "name": "APK-Inform",
  "config": {"parser_type": "apk_inform", "regions": ["Odesa"]}
}'
# Response: {"id": 1, ...}

# 2. Ingest
curl -X POST "http://localhost:8001/ingestion/start" -d '{
  "data_source_id": 1,
  "layer": "bronze"
}'
# Response: {"job_id": "job_abc123", "status": "started"}

# 3. Check
curl -X GET "http://localhost:8001/ingestion/jobs/job_abc123"
# Response: {"status": "completed", "records_written": 150, ...}
```

---

## When to Add New Parser

1. ✅ Create parser class inheriting BaseParser
2. ✅ Add to ParserFactory.PARSER_REGISTRY
3. ✅ Add config validation rules to ConfigValidator
4. ✅ Update get_supported_parsers() info
5. ✅ Test with sample DataSource

That's it! No other code changes needed.
