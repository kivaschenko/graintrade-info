# Parser Configuration & Pipeline Integration - Implementation Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Data Source Model](#data-source-model)
3. [Parser Factory Pattern](#parser-factory-pattern)
4. [Configuration Validation](#configuration-validation)
5. [Pipeline Integration](#pipeline-integration)
6. [Adding New Parsers](#adding-new-parsers)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Architecture                     │
└─────────────────────────────────────────────────────────────┘

User/API Request
       │
       ▼
┌──────────────────────────┐
│ DataSource Registration  │
│  (with config JSON)      │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Ingestion Router         │
│  /ingestion/start        │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ ConfigValidator          │
│  (validate config)       │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ ParserFactory            │
│  (instantiate parser)    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Parser Instance          │
│  (execute parse())       │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Result Storage           │
│  (bronze/silver/gold)    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ IngestionLog Update      │
│  (track job results)     │
└──────────────────────────┘
```

---

## Data Source Model

### Current Structure

```python
class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True)
    source_type = Column(String(50))  # csv, json, api, web_scraping
    description = Column(Text)
    
    # Connection details
    url = Column(String(500))
    file_path = Column(String(500))
    api_endpoint = Column(String(500))
    credentials_required = Column(Boolean)
    
    # Parser Configuration - Key Field
    config = Column(JSON)  # ← Stores parser parameters here
    
    # Scheduling
    update_frequency = Column(String(50))
    last_ingestion = Column(DateTime)
    next_scheduled_ingestion = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### Config Field Structure

The `config` JSON field stores all parser-specific parameters:

```python
config = {
    "parser_type": "apk_inform",  # REQUIRED: identifies parser
    "regions": ["Odesa", "Mykolaiv"],  # Parser-specific params
    "upload_to_storage": True,
    "storage_type": "hetzner",
    "retry_attempts": 3,
    # Add any other params needed by the parser
}
```

---

## Parser Factory Pattern

### Purpose

The ParserFactory abstracts parser instantiation:
- Eliminates direct imports in business logic
- Enables dynamic parser selection
- Supports easy addition of new parsers
- Provides clear error handling

### Implementation

```python
class ParserFactory:
    PARSER_REGISTRY: Dict[str, type] = {
        "apk_inform": APKInformParser,
        "investing_com": InvestingComParser,
        "tripoli_land": TripoliLandParser,
        "yfinance": YFinanceParser,
        # Add more parsers here
    }
    
    @classmethod
    def create_parser(cls, data_source: DataSource) -> BaseParser:
        """Factory method that creates parser from DataSource"""
        parser_type = data_source.config.get("parser_type")
        
        if parser_type not in cls.PARSER_REGISTRY:
            raise ValueError(f"Unknown parser: {parser_type}")
        
        return cls._instantiate_parser(
            cls.PARSER_REGISTRY[parser_type],
            data_source.config
        )
```

### Usage in Pipeline

```python
# Before: Direct instantiation (tightly coupled)
parser = APKInformParser(regions=["Odesa"])

# After: Factory pattern (loosely coupled)
data_source = db.query(DataSource).filter_by(id=1).first()
parser = ParserFactory.create_parser(data_source)
```

---

## Configuration Validation

### Why Validate?

- Catch config errors early before execution
- Provide clear error messages to users
- Prevent runtime failures
- Type-check field values

### Validation Rules

```python
class ConfigValidator:
    REQUIRED_FIELDS = {
        "apk_inform": ["parser_type"],
        "investing_com": ["parser_type", "instruments"],
        "yfinance": ["parser_type", "tickers"],
    }
    
    FIELD_TYPES = {
        "apk_inform": {
            "parser_type": str,
            "regions": list,
            "upload_to_storage": bool,
        },
        # ... more rules
    }
```

### Usage

```python
# Validate config
is_valid, errors = ConfigValidator.validate(data_source.config)

if not is_valid:
    return {"status": "failed", "errors": errors}
```

---

## Pipeline Integration

### Current Ingestion Flow

```python
# Old: Traditional file/API ingestion only
def run_ingestion_job(data_source_id, layer):
    data_source = get_data_source(data_source_id)
    
    if layer == "bronze":
        # Only supports file paths and URLs
        result = ingest_to_bronze(
            source_path=data_source.file_path or data_source.url,
            source_format=data_source.source_type
        )
```

### Enhanced Ingestion Flow

```python
# New: Parser-aware ingestion
def run_ingestion_job_with_parser(data_source_id, layer):
    data_source = get_data_source(data_source_id)
    
    if layer == "bronze":
        # Try parser first if configured
        if data_source.config and data_source.config.get("parser_type"):
            # Validate
            is_valid, errors = ConfigValidator.validate(data_source.config)
            if not is_valid:
                raise ValueError(f"Invalid config: {errors}")
            
            # Create and execute parser
            parser = ParserFactory.create_parser(data_source)
            df = parser.parse()
            
            # Store result
            store_to_bronze(df, data_source.name)
        else:
            # Fallback to traditional ingestion
            ingest_to_bronze(data_source.file_path or data_source.url)
    
    # Update tracking
    update_ingestion_log(data_source_id, results)
```

### Integration Points

1. **Ingestion Router** - Accept ingestion requests
2. **Config Validator** - Validate data source config
3. **Parser Factory** - Create parser instances
4. **Parser Execution** - Run parse() method
5. **Storage Layer** - Save results to bronze/silver/gold
6. **Logging** - Track job progress and results

---

## Adding New Parsers

### Step 1: Create Parser Class

```python
# app/parser_services/myparser.py

from app.parser_services.base_parser import BaseParser
from typing import List, Dict, Any
import pandas as pd

class MyParser(BaseParser):
    def __init__(self, custom_param: str):
        self.custom_param = custom_param
    
    def parse(self) -> pd.DataFrame:
        """Execute parsing logic"""
        # Fetch data
        data = self._fetch_data()
        
        # Transform to standard schema
        df = pd.DataFrame(data)
        
        return df
    
    def _fetch_data(self) -> List[Dict[str, Any]]:
        """Custom fetch logic"""
        pass
```

### Step 2: Register in ParserFactory

```python
# app/services/parser_factory.py

from app.parser_services.myparser import MyParser

class ParserFactory:
    PARSER_REGISTRY = {
        "myparser": MyParser,  # Add this line
        # ... other parsers
    }
    
    @classmethod
    def _instantiate_parser(cls, parser_class, config):
        # ... existing code ...
        
        elif parser_type == "myparser":
            custom_param = config.get("custom_param", "default")
            return parser_class(custom_param=custom_param)
```

### Step 3: Add Config Validation Rules

```python
# app/services/config_validator.py

class ConfigValidator:
    REQUIRED_FIELDS = {
        "myparser": ["parser_type", "custom_param"],  # Add this
    }
    
    FIELD_TYPES = {
        "myparser": {  # Add this
            "parser_type": str,
            "custom_param": str,
        }
    }
    
    # Add parser-specific validation
    def _validate_parser_specific(parser_type, config):
        if parser_type == "myparser":
            if config.get("custom_param") not in ["value1", "value2"]:
                errors.append("custom_param must be 'value1' or 'value2'")
```

### Step 4: Register in Supported Parsers Info

```python
class ParserFactory:
    @classmethod
    def get_supported_parsers(cls):
        return {
            "myparser": {
                "description": "My custom parser",
                "source_type": "api",
                "required_config": ["parser_type", "custom_param"],
                "optional_config": ["retry_attempts"]
            },
            # ... other parsers
        }
```

### Step 5: Create DataSource

```bash
curl -X POST "http://localhost:8001/data-sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Data Source",
    "source_type": "api",
    "config": {
      "parser_type": "myparser",
      "custom_param": "value1"
    }
  }'
```

---

## Monitoring & Troubleshooting

### IngestionLog Schema

```python
class IngestionLog(Base):
    __tablename__ = "ingestion_logs"
    
    id = Column(Integer, primary_key=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"))
    job_id = Column(String(50), unique=True)
    status = Column(String(20))  # started, running, completed, failed
    layer = Column(String(20))  # bronze, silver, gold
    
    records_read = Column(Integer)
    records_written = Column(Integer)
    records_failed = Column(Integer)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    output_path = Column(String(500))
    error_message = Column(Text)
    
    # Audit trail
    created_by = Column(String(100))
    updated_by = Column(String(100))
```

### Monitoring Queries

```sql
-- Check job status
SELECT * FROM ingestion_logs 
WHERE job_id = 'job_a1b2c3d4e5f6';

-- Find failed jobs
SELECT * FROM ingestion_logs 
WHERE status = 'failed' 
ORDER BY started_at DESC;

-- Get statistics by data source
SELECT 
    data_source_id,
    COUNT(*) as total_jobs,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
    SUM(records_written) as total_records
FROM ingestion_logs
GROUP BY data_source_id;

-- Check execution time
SELECT 
    job_id,
    data_source_id,
    layer,
    EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
FROM ingestion_logs
WHERE status = 'completed'
ORDER BY started_at DESC
LIMIT 10;
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Unknown parser type" | parser_type not registered | Check ParserFactory.PARSER_REGISTRY |
| "Missing required fields" | Incomplete config | Add required fields from ConfigValidator.REQUIRED_FIELDS |
| "Parser returned empty data" | Website down or parsing failed | Check logs, verify website accessibility |
| "Connection timeout" | Network issue | Check API endpoint, firewall rules |
| "Empty DataFrame" | No matching data | Adjust config parameters, check data source |

### Logging

Enable debug logging to troubleshoot:

```python
# app/config.py
LOG_LEVEL = "DEBUG"  # Enables detailed logs

# In code
from app.logger import logger

logger.debug(f"Parser config: {data_source.config}")
logger.info(f"Created {parser_type} parser")
logger.error(f"Parser failed: {error}", exc_info=True)
```

### Example Log Output

```
2024-01-12 10:30:00 INFO Starting parser: APK-Inform Odesa
2024-01-12 10:30:00 DEBUG Parser config: {'parser_type': 'apk_inform', 'regions': ['Odesa']}
2024-01-12 10:30:00 INFO Config validation passed for apk_inform
2024-01-12 10:30:00 INFO Created apk_inform parser for DataSource 'APK-Inform Odesa'
2024-01-12 10:30:05 INFO Parser APK-Inform Odesa completed: 150 records
2024-01-12 10:30:05 INFO Saved APK-Inform data to /data/delta/bronze/apk_inform_odesa_raw
2024-01-12 10:30:06 INFO Ingestion job job_a1b2c3d4e5f6 completed with status: completed
```

---

## Complete End-to-End Example

### 1. Register Data Source

```bash
POST /data-sources
{
  "name": "APK-Inform Prices",
  "source_type": "web_scraping",
  "config": {
    "parser_type": "apk_inform",
    "regions": ["Odesa", "Mykolaiv"]
  }
}
```

### 2. Start Ingestion Job

```bash
POST /ingestion/start
{
  "data_source_id": 1,
  "layer": "bronze"
}
```

### 3. Pipeline Execution

```
Request → Router → Validator → Factory → Parser → Storage → Log
  ↓         ✓         ✓         ✓        ✓        ✓        ✓
Job runs asynchronously, returns job_id immediately
```

### 4. Check Status

```bash
GET /ingestion/jobs/job_a1b2c3d4e5f6
{
  "job_id": "job_a1b2c3d4e5f6",
  "status": "completed",
  "records_read": 150,
  "records_written": 150,
  "output_path": "/data/delta/bronze/apk_inform_prices_raw"
}
```

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `PARSER_CONFIG_GUIDE.md` | Main documentation |
| `PARSER_USAGE_EXAMPLES.md` | Practical examples |
| `app/services/parser_factory.py` | Parser instantiation logic |
| `app/services/config_validator.py` | Config validation rules |
| `app/routers/ingestion_router_enhanced.py` | Enhanced ingestion with parsers |

---

## Summary

**Key Concepts:**

1. **DataSource.config** - Stores parser parameters as JSON
2. **ParserFactory** - Creates parser instances dynamically
3. **ConfigValidator** - Validates configuration before execution
4. **Pipeline Integration** - Seamlessly integrates with existing ingestion
5. **Monitoring** - Track all jobs via IngestionLog

**Flow:**
```
DataSource (with config) 
    ↓
Ingestion Request
    ↓
Config Validation
    ↓
Parser Factory (instantiate)
    ↓
Parser Execution
    ↓
Store Results
    ↓
Update Log & Status
```

**Benefits:**
- ✅ No code changes to add/modify parser configurations
- ✅ Flexible JSON config for any parser-specific parameters
- ✅ Type-safe configuration validation
- ✅ Clean separation of concerns
- ✅ Full audit trail with IngestionLog
- ✅ Easy to add new parsers
- ✅ Production-ready with error handling
