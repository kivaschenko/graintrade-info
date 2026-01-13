# Example: Practical Parser Configuration & Usage

This directory contains practical examples of using the Parser Configuration System.

## Quick Start

### 1. Register a Data Source with Parser Config

```bash
# Register APK-Inform parser with specific regions
curl -X POST "http://localhost:8001/data-sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "APK-Inform Odesa",
    "source_type": "web_scraping",
    "description": "Daily grain prices from APK-Inform for Odesa region",
    "update_frequency": "daily",
    "config": {
      "parser_type": "apk_inform",
      "regions": ["Odesa", "Mykolaiv"],
      "upload_to_storage": true,
      "storage_type": "hetzner"
    },
    "is_active": true
  }'
```

Response (note the data_source_id):
```json
{
  "id": 1,
  "name": "APK-Inform Odesa",
  "config": {
    "parser_type": "apk_inform",
    "regions": ["Odesa", "Mykolaiv"],
    ...
  }
}
```

### 2. Start Ingestion Job

```bash
curl -X POST "http://localhost:8001/ingestion/start" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source_id": 1,
    "layer": "bronze"
  }'
```

Response:
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "status": "started"
}
```

### 3. Check Job Status

```bash
curl -X GET "http://localhost:8001/ingestion/jobs/job_a1b2c3d4e5f6"
```

## Configuration Examples by Parser

### APK-Inform Parser

Fetches grain prices from https://www.apk-inform.com

**Minimal Config:**
```json
{
  "parser_type": "apk_inform"
}
```

**Full Config:**
```json
{
  "parser_type": "apk_inform",
  "regions": ["Odesa", "Mykolaiv", "Kherson", "Zaporizhzhia"],
  "upload_to_storage": true,
  "storage_type": "hetzner"
}
```

**Data Source Creation:**
```bash
curl -X POST "http://localhost:8001/data-sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "APK-Inform All Regions",
    "source_type": "web_scraping",
    "update_frequency": "daily",
    "config": {
      "parser_type": "apk_inform",
      "regions": ["Odesa", "Mykolaiv", "Kherson"],
      "upload_to_storage": true,
      "storage_type": "hetzner"
    }
  }'
```

---

### Investing.com Parser

Fetches financial data from Investing.com

**Config:**
```json
{
  "parser_type": "investing_com",
  "instruments": [
    {
      "name": "Wheat CBOT",
      "symbol": "ZWZ",
      "country": "usa",
      "type": "futures"
    },
    {
      "name": "Corn CBOT",
      "symbol": "ZCZ",
      "country": "usa",
      "type": "futures"
    }
  ],
  "start_date": "2023-01-01",
  "end_date": "2024-01-12",
  "retry_attempts": 3
}
```

**Data Source Creation:**
```bash
curl -X POST "http://localhost:8001/data-sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Investing.com Futures",
    "source_type": "api",
    "api_endpoint": "https://investing.com",
    "update_frequency": "daily",
    "config": {
      "parser_type": "investing_com",
      "instruments": [
        {
          "name": "Wheat CBOT",
          "symbol": "ZWZ",
          "country": "usa",
          "type": "futures"
        }
      ],
      "start_date": "2023-01-01",
      "end_date": "2024-01-12"
    }
  }'
```

---

### YFinance Parser

Fetches market data from Yahoo Finance

**Config:**
```json
{
  "parser_type": "yfinance",
  "tickers": ["ZWZ=F", "ZCZ=F", "SOYB=F"],
  "period": "2y",
  "interval": "1d",
  "progress": false
}
```

**Data Source Creation:**
```bash
curl -X POST "http://localhost:8001/data-sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Yahoo Finance Commodities",
    "source_type": "api",
    "api_endpoint": "https://finance.yahoo.com",
    "update_frequency": "daily",
    "config": {
      "parser_type": "yfinance",
      "tickers": ["ZWZ=F", "ZCZ=F", "SOYB=F"],
      "period": "2y",
      "interval": "1d"
    }
  }'
```

---

### Tripoli Land Parser

Fetches prices from Ukrainian grain trading platform

**Config:**
```json
{
  "parser_type": "tripoli_land",
  "companies": ["nibulon", "kernel", "lnz-group", "tas-agro"],
  "base_url": "https://tripoli.land",
  "storage_type": "hetzner",
  "output_format": "csv"
}
```

**Data Source Creation:**
```bash
curl -X POST "http://localhost:8001/data-sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tripoli Land Prices",
    "source_type": "web_scraping",
    "update_frequency": "daily",
    "config": {
      "parser_type": "tripoli_land",
      "companies": ["nibulon", "kernel", "lnz-group"],
      "base_url": "https://tripoli.land"
    }
  }'
```

---

## Managing Data Sources

### Update Parser Config

```bash
curl -X PATCH "http://localhost:8001/data-sources/1" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "parser_type": "apk_inform",
      "regions": ["Odesa", "Mykolaiv", "Kherson", "Zaporizhzhia", "Poltava"],
      "upload_to_storage": true
    }
  }'
```

### Activate/Deactivate Data Source

```bash
curl -X PATCH "http://localhost:8001/data-sources/1" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

### List All Data Sources

```bash
curl -X GET "http://localhost:8001/data-sources"
```

---

## Advanced Usage

### Get Supported Parsers

Get information about all available parsers:

```bash
curl -X GET "http://localhost:8001/ingestion/parsers"
```

Response:
```json
{
  "apk_inform": {
    "description": "APK-Inform Ukrainian grain prices",
    "source_type": "web_scraping",
    "required_config": ["parser_type"],
    "optional_config": ["regions", "upload_to_storage", "storage_type"]
  },
  "investing_com": {
    "description": "Investing.com financial data",
    "source_type": "api",
    "required_config": ["parser_type", "instruments"],
    "optional_config": ["start_date", "end_date", "retry_attempts"]
  },
  ...
}
```

### Check Ingestion Job Status with Details

```bash
curl -X GET "http://localhost:8001/ingestion/jobs?data_source_id=1&status=completed&limit=10"
```

Response:
```json
[
  {
    "job_id": "job_a1b2c3d4e5f6",
    "data_source_id": 1,
    "status": "completed",
    "layer": "bronze",
    "records_read": 150,
    "records_written": 150,
    "records_failed": 0,
    "output_path": "/data/delta/bronze/apk_inform_odesa_raw",
    "started_at": "2024-01-12T10:30:00",
    "completed_at": "2024-01-12T10:35:00"
  }
]
```

---

## Python Usage Examples

### Direct Factory Usage

```python
from app.models import DataSource
from app.services.parser_factory import ParserFactory
from sqlalchemy.orm import Session

def run_parser(db: Session, data_source_id: int):
    """Execute parser from DataSource"""
    
    # Get data source
    data_source = db.query(DataSource).filter(
        DataSource.id == data_source_id
    ).first()
    
    # Create parser from config
    parser = ParserFactory.create_parser(data_source)
    
    # Parse data
    df = parser.parse()
    
    print(f"Fetched {len(df)} records")
    return df
```

### With Config Validation

```python
from app.services.config_validator import ConfigValidator
from app.services.parser_factory import ParserFactory

def safe_parse(data_source):
    """Execute parser with validation"""
    
    # Validate config first
    is_valid, errors = ConfigValidator.validate(data_source.config)
    
    if not is_valid:
        print(f"Config validation failed: {errors}")
        return None
    
    # Create and execute parser
    parser = ParserFactory.create_parser(data_source)
    return parser.parse()
```

### Create DataSource Programmatically

```python
from app.models import DataSource
from sqlalchemy.orm import Session

def create_apk_inform_source(db: Session, regions: list):
    """Create APK-Inform data source with regions"""
    
    data_source = DataSource(
        name=f"APK-Inform {'-'.join(regions)}",
        source_type="web_scraping",
        description=f"Daily prices for {', '.join(regions)}",
        update_frequency="daily",
        config={
            "parser_type": "apk_inform",
            "regions": regions,
            "upload_to_storage": True,
            "storage_type": "hetzner"
        },
        is_active=True
    )
    
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    
    return data_source
```

---

## Troubleshooting

### Invalid Config Error

**Error:**
```
Config validation error: Missing required fields for yfinance: ['tickers']
```

**Solution:** Add required fields to config
```bash
curl -X PATCH "http://localhost:8001/data-sources/1" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "parser_type": "yfinance",
      "tickers": ["ZWZ=F", "ZCZ=F"]
    }
  }'
```

### Parser Type Not Found

**Error:**
```
Unknown parser type: 'unknown_parser'
```

**Solution:** Check available parsers or register the correct parser type
```bash
curl -X GET "http://localhost:8001/ingestion/parsers"
```

### Empty Data Result

**Error:** Parser returned empty DataFrame

**Solution:** 
1. Check parser-specific documentation (e.g., website accessibility)
2. Verify config parameters
3. Check parser logs for details

---

## Summary

**Flow:**
1. Create DataSource with `config` containing parser parameters
2. Trigger ingestion job with DataSource ID
3. ParserFactory reads config and instantiates parser
4. Parser executes and returns data
5. Data is stored in bronze layer
6. Check job status via API

**Benefits:**
- No code changes needed to add/modify parser configurations
- Flexible JSON config supports any parser-specific parameters
- ConfigValidator ensures config integrity
- ParserFactory abstracts parser instantiation logic
- Audit trail via IngestionLog with full job history
