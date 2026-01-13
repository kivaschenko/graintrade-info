# Parser Configuration Guide

## Overview

The `DataSource` model's `config` field stores flexible JSON configuration for each parser. This guide shows how to:

1. **Save parser parameters** to the `config` column
2. **Retrieve and use** those parameters in your pipeline
3. **Create parser instances** dynamically based on DataSource configs

---

## 1. DataSource Model Structure

The `config` field is a JSON column that stores parser-specific parameters:

```python
class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # csv, json, api, telegram, web_scraping
    config = Column(JSON)  # <-- Store flexible parser config here
    url = Column(String(500))
    file_path = Column(String(500))
    is_active = Column(Boolean, default=True)
    # ... other fields
```

---

## 2. Example Configurations for Different Parsers

### APK-Inform Parser Config

```json
{
  "parser_type": "apk_inform",
  "regions": ["Odesa", "Mykolaiv", "Kherson"],
  "upload_to_storage": true,
  "storage_type": "hetzner"
}
```

**API Registration:**
```bash
curl -X POST "http://localhost:8001/data-sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "APK-Inform Prices",
    "source_type": "web_scraping",
    "description": "Ukrainian grain market prices",
    "update_frequency": "daily",
    "config": {
      "parser_type": "apk_inform",
      "regions": ["Odesa", "Mykolaiv", "Kherson"],
      "upload_to_storage": true,
      "storage_type": "hetzner"
    },
    "is_active": true
  }'
```

### Investing.com Parser Config

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

**API Registration:**
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
      "end_date": "2024-01-12",
      "retry_attempts": 3
    }
  }'
```

### Tripoli Land Parser Config

```json
{
  "parser_type": "tripoli_land",
  "companies": ["nibulon", "kernel", "lnz-group", "tas-agro"],
  "base_url": "https://tripoli.land",
  "storage_type": "hetzner",
  "output_format": "csv"
}
```

### YFinance Parser Config

```json
{
  "parser_type": "yfinance",
  "tickers": ["ZWZ=F", "ZCZ=F", "SOYB=F"],
  "period": "2y",
  "interval": "1d",
  "progress": false
}
```

---

## 3. Using Parser Config in the Pipeline

### Option A: Direct Parser Instantiation

Retrieve DataSource and pass config to parser:

```python
from sqlalchemy.orm import Session
from app.models import DataSource
from app.parser_services import (
    APKInformParser,
    InvestingComParser,
    TripoliLandParser,
    YFinanceParser
)

def run_parser_for_data_source(db: Session, data_source_id: int):
    """Execute parser based on DataSource configuration"""
    
    data_source = db.query(DataSource).filter(
        DataSource.id == data_source_id
    ).first()
    
    if not data_source or not data_source.is_active:
        return None
    
    parser_type = data_source.config.get("parser_type")
    
    # Instantiate parser based on type
    if parser_type == "apk_inform":
        regions = data_source.config.get("regions", [])
        parser = APKInformParser(regions=regions)
        df = parser.parse()
        
    elif parser_type == "investing_com":
        instruments = data_source.config.get("instruments", [])
        start_date = data_source.config.get("start_date")
        end_date = data_source.config.get("end_date")
        parser = InvestingComParser(
            instrument_cfg=instruments[0] if instruments else {},
            start_date=start_date,
            end_date=end_date
        )
        df = parser.parse()
        
    elif parser_type == "tripoli_land":
        companies = data_source.config.get("companies", [])
        parser = TripoliLandParser(companies=companies)
        df = parser.parse()
        
    elif parser_type == "yfinance":
        tickers = data_source.config.get("tickers", [])
        period = data_source.config.get("period", "2y")
        parser = YFinanceParser(tickers=tickers, period=period)
        df = parser.parse()
    
    else:
        raise ValueError(f"Unknown parser type: {parser_type}")
    
    return df
```

### Option B: Factory Pattern (Recommended)

Create a ParserFactory for cleaner code:

```python
# app/services/parser_factory.py
from typing import Dict, Any
from app.models import DataSource
from app.parser_services import (
    APKInformParser,
    InvestingComParser,
    TripoliLandParser,
    YFinanceParser,
    BaseParser
)
from app.logger import logger


class ParserFactory:
    """Factory for instantiating parsers based on DataSource config"""
    
    PARSER_REGISTRY = {
        "apk_inform": APKInformParser,
        "investing_com": InvestingComParser,
        "tripoli_land": TripoliLandParser,
        "yfinance": YFinanceParser,
    }
    
    @staticmethod
    def create_parser(data_source: DataSource) -> BaseParser:
        """
        Create a parser instance from DataSource configuration
        
        Args:
            data_source: DataSource model instance with config
            
        Returns:
            Initialized parser instance
            
        Raises:
            ValueError: If parser_type is unknown or config is invalid
        """
        if not data_source.config:
            raise ValueError(f"DataSource {data_source.name} has no config")
        
        parser_type = data_source.config.get("parser_type")
        
        if parser_type not in ParserFactory.PARSER_REGISTRY:
            raise ValueError(f"Unknown parser type: {parser_type}")
        
        parser_class = ParserFactory.PARSER_REGISTRY[parser_type]
        
        try:
            # Instantiate with config parameters
            parser = ParserFactory._instantiate_parser(parser_class, data_source.config)
            logger.info(f"Created {parser_type} parser for {data_source.name}")
            return parser
            
        except Exception as e:
            logger.error(f"Failed to create parser for {data_source.name}: {e}")
            raise
    
    @staticmethod
    def _instantiate_parser(parser_class, config: Dict[str, Any]) -> BaseParser:
        """Instantiate specific parser with config parameters"""
        
        parser_type = config.get("parser_type")
        
        if parser_type == "apk_inform":
            return parser_class(regions=config.get("regions", []))
        
        elif parser_type == "investing_com":
            instruments = config.get("instruments", [])
            return parser_class(
                instrument_cfg=instruments[0] if instruments else {},
                start_date=config.get("start_date"),
                end_date=config.get("end_date")
            )
        
        elif parser_type == "tripoli_land":
            return parser_class(companies=config.get("companies", []))
        
        elif parser_type == "yfinance":
            return parser_class(
                tickers=config.get("tickers", []),
                period=config.get("period", "2y")
            )
        
        else:
            raise ValueError(f"Unknown parser type: {parser_type}")
```

### Option C: Using in Ingestion Pipeline

Integrate with the existing ingestion router:

```python
# app/routers/ingestion_router.py (modified)

from app.services.parser_factory import ParserFactory
from app.models import DataSource, IngestionLog

def run_ingestion_job(
    job_id: str,
    data_source_id: int,
    layer: str,
    db_url: str
):
    """Enhanced ingestion job that uses parser factory"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get data source
        data_source = db.query(DataSource).filter(
            DataSource.id == data_source_id
        ).first()
        
        if not data_source:
            logger.error(f"Data source {data_source_id} not found")
            return
        
        # Create ingestion log
        log = IngestionLog(
            data_source_id=data_source_id,
            job_id=job_id,
            status="running",
            layer=layer,
            started_at=datetime.now()
        )
        db.add(log)
        db.commit()
        
        result = {}
        
        if layer == "bronze":
            # Try using parser factory first
            if data_source.config and data_source.config.get("parser_type"):
                try:
                    parser = ParserFactory.create_parser(data_source)
                    df = parser.parse()
                    
                    # Save to bronze layer
                    result = {
                        "status": "completed",
                        "records_read": len(df),
                        "records_written": len(df),
                        "records_removed": 0
                    }
                    
                except Exception as e:
                    logger.error(f"Parser execution failed: {e}")
                    result = {
                        "status": "failed",
                        "error": str(e)
                    }
            else:
                # Fallback to traditional ingestion
                result = ingest_to_bronze(
                    source_path=data_source.file_path or data_source.url,
                    source_format=data_source.source_type,
                    source_name=data_source.name,
                    table_name=f"{data_source.name}_raw"
                )
        
        # Update log with results
        log.status = result.get("status", "completed")
        log.records_read = result.get("records_read", 0)
        log.records_written = result.get("records_written", 0)
        log.completed_at = datetime.now()
        
        if result.get("status") == "failed":
            log.error_message = result.get("error")
        
        db.commit()
        logger.info(f"Ingestion job {job_id} completed")
        
    except Exception as e:
        logger.error(f"Ingestion job {job_id} failed: {str(e)}")
        if log:
            log.status = "failed"
            log.error_message = str(e)
            db.commit()
    
    finally:
        db.close()
```

---

## 4. Complete Example: End-to-End Workflow

### Step 1: Register DataSource with Config

```bash
curl -X POST "http://localhost:8001/data-sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "APK-Inform Odesa Prices",
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

Response:
```json
{
  "id": 1,
  "name": "APK-Inform Odesa Prices",
  "source_type": "web_scraping",
  "config": {
    "parser_type": "apk_inform",
    "regions": ["Odesa", "Mykolaiv"],
    "upload_to_storage": true,
    "storage_type": "hetzner"
  }
}
```

### Step 2: Start Ingestion Job

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
  "data_source_id": 1,
  "status": "started",
  "layer": "bronze"
}
```

### Step 3: Check Job Status

```bash
curl -X GET "http://localhost:8001/ingestion/jobs/job_a1b2c3d4e5f6"
```

Response:
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "data_source_id": 1,
  "status": "completed",
  "layer": "bronze",
  "records_read": 150,
  "records_written": 150,
  "records_failed": 0,
  "output_path": "/data/delta/bronze/apk_inform_odesa_prices_raw",
  "started_at": "2024-01-12T10:30:00",
  "completed_at": "2024-01-12T10:35:00"
}
```

---

## 5. Config Schema Best Practices

### Required Fields by Parser Type

| Parser Type | Required Config Fields | Optional Fields |
|------------|----------------------|-----------------|
| `apk_inform` | `parser_type` | `regions`, `upload_to_storage`, `storage_type` |
| `investing_com` | `parser_type`, `instruments` | `start_date`, `end_date`, `retry_attempts` |
| `tripoli_land` | `parser_type` | `companies`, `base_url`, `storage_type` |
| `yfinance` | `parser_type`, `tickers` | `period`, `interval`, `progress` |

### Validation Example

```python
# app/services/config_validator.py
from typing import Dict, Any
from app.logger import logger

class ConfigValidator:
    """Validate DataSource config based on parser type"""
    
    REQUIRED_FIELDS = {
        "apk_inform": ["parser_type"],
        "investing_com": ["parser_type", "instruments"],
        "tripoli_land": ["parser_type"],
        "yfinance": ["parser_type", "tickers"],
    }
    
    @staticmethod
    def validate(config: Dict[str, Any]) -> bool:
        """
        Validate config has all required fields
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        if not config:
            logger.warning("Config is empty")
            return False
        
        parser_type = config.get("parser_type")
        required = ConfigValidator.REQUIRED_FIELDS.get(parser_type, [])
        
        missing = [field for field in required if field not in config]
        
        if missing:
            logger.error(f"Missing required fields for {parser_type}: {missing}")
            return False
        
        logger.info(f"Config validation passed for {parser_type}")
        return True
```

---

## 6. Dynamic Parameter Updates

Update parser config without recreating DataSource:

```bash
curl -X PATCH "http://localhost:8001/data-sources/1" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "parser_type": "apk_inform",
      "regions": ["Odesa", "Mykolaiv", "Kherson", "Zaporizhzhia"],
      "upload_to_storage": true,
      "storage_type": "hetzner"
    }
  }'
```

---

## 7. Monitoring & Logging

Track parser execution with structured logging:

```python
from app.logger import logger

def run_parser_with_monitoring(data_source: DataSource):
    """Execute parser with comprehensive logging"""
    
    logger.info(f"Starting parser: {data_source.name}")
    logger.debug(f"Parser config: {data_source.config}")
    
    try:
        parser = ParserFactory.create_parser(data_source)
        df = parser.parse()
        
        logger.info(f"Parser {data_source.name} completed")
        logger.info(f"Records fetched: {len(df)}")
        
        return df
        
    except Exception as e:
        logger.error(f"Parser {data_source.name} failed: {e}", exc_info=True)
        raise
```

---

## Summary

**Best Practice Flow:**

1. **Register DataSource** with `config` containing `parser_type` + parser-specific parameters
2. **Use ParserFactory** to instantiate parser from config
3. **Execute parser** in ingestion job
4. **Store results** in appropriate data layer (bronze/silver/gold)
5. **Update DataSource** with `last_ingestion` timestamp
6. **Monitor via IngestionLog** for job status and error handling

This approach allows **flexible parser configuration without code changes**.
