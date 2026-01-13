# Simplified Ingestion Service - Reference Implementation

This shows what the code should look like if simplified to KISS principle.

## File: `app/services/ingestion_service.py`

```python
"""
Ingestion Service - Simplified orchestrator (NOT a factory pattern)

This replaces the factory pattern approach with direct, simple parser usage.
Configuration comes from environment variables, not database JSON.
"""
from typing import Dict, Any
from datetime import datetime
import uuid

from app.parsers import (
    APKInformParser,
    InvestingComParser,
    YFinanceParser,
    TripoliLandParser,
    CurrencyParser,
    GraintradeComuaParser,
)
from app.config import settings
from app.logger import logger
from app.models import IngestionLog, DataSource
from sqlalchemy.orm import Session


# Initialize parsers with configuration from environment variables
# This replaces ParserFactory.PARSER_REGISTRY
AVAILABLE_PARSERS = {
    "apk_inform": APKInformParser,
    "investing_com": InvestingComParser,
    "yfinance": YFinanceParser,
    "tripoli_land": TripoliLandParser,
    "currency": CurrencyParser,
    "graintradecomua": GraintradeComuaParser,
}


def get_parser_instance(parser_name: str):
    """
    Get an initialized parser instance.
    
    Args:
        parser_name: One of: apk_inform, investing_com, yfinance, tripoli_land, currency, graintradecomua
        
    Returns:
        Instantiated parser ready to use
        
    Raises:
        ValueError: If parser_name is not recognized
    """
    if parser_name not in AVAILABLE_PARSERS:
        raise ValueError(
            f"Unknown parser: {parser_name}. "
            f"Available: {', '.join(AVAILABLE_PARSERS.keys())}"
        )
    
    parser_class = AVAILABLE_PARSERS[parser_name]
    
    # Create parser with configuration from environment variables
    # This replaces ConfigValidator entirely - just pass what you have
    if parser_name == "apk_inform":
        return APKInformParser(
            regions=settings.APK_REGIONS.split(","),
            upload_to_storage=settings.APK_UPLOAD_STORAGE,
            storage_type=settings.APK_STORAGE_TYPE,
        )
    
    elif parser_name == "investing_com":
        return InvestingComParser(
            instruments=settings.IC_INSTRUMENTS.split(","),
            start_date=settings.IC_START_DATE,
            end_date=settings.IC_END_DATE or None,
            retry_attempts=settings.IC_RETRY_ATTEMPTS,
        )
    
    elif parser_name == "yfinance":
        return YFinanceParser(
            tickers=settings.YF_TICKERS.split(","),
            period=settings.YF_PERIOD,
            interval=settings.YF_INTERVAL,
            progress=settings.ENV == "development",
        )
    
    elif parser_name == "tripoli_land":
        return TripoliLandParser(
            companies=settings.TL_COMPANIES.split(","),
            base_url=settings.TL_BASE_URL,
            storage_type=settings.TL_STORAGE_TYPE,
            output_format=settings.TL_OUTPUT_FORMAT,
        )
    
    elif parser_name == "currency":
        return CurrencyParser(
            symbols=settings.CURR_SYMBOLS.split(","),
            intervals=settings.CURR_INTERVALS.split(","),
        )
    
    elif parser_name == "graintradecomua":
        return GraintradeComuaParser(
            base_url=settings.GT_BASE_URL,
            api_key=settings.GT_API_KEY,
            timeout=settings.GT_TIMEOUT,
        )


def run_ingestion(
    parser_name: str,
    job_id: str,
    db: Session,
    layer: str = "bronze"
):
    """
    Execute an ingestion job.
    
    This is the main ingestion orchestrator. It:
    1. Gets the parser
    2. Runs data collection
    3. Stores in Delta Lake
    4. Updates job log
    5. Publishes to Telegram
    6. Handles errors gracefully
    
    Args:
        parser_name: Name of parser to use
        job_id: Unique job identifier
        db: Database session
        layer: Data layer (bronze, silver, gold)
    """
    log = None
    
    try:
        # Get or create job log
        log = db.query(IngestionLog).filter(IngestionLog.job_id == job_id).first()
        if not log:
            log = IngestionLog(
                job_id=job_id,
                parser_name=parser_name,
                status="running",
                layer=layer,
                started_at=datetime.now(),
            )
            db.add(log)
            db.commit()
        
        logger.info(f"Starting ingestion job {job_id} with parser: {parser_name}")
        
        # Get parser instance
        parser = get_parser_instance(parser_name)
        
        # Execute parser
        logger.info(f"Parser {parser_name} starting data collection...")
        raw_data = parser.parse()
        
        records_read = len(raw_data) if isinstance(raw_data, list) else 1
        logger.info(f"Parser {parser_name} collected {records_read} records")
        
        # Store in appropriate layer
        if layer == "bronze":
            # Store raw data in bronze layer
            output_path = f"{settings.BRONZE_LAYER_PATH}/{parser_name}_{datetime.now().isoformat()}"
            # Use Spark to write
            records_written = _write_bronze_layer(parser_name, raw_data, output_path)
        elif layer == "silver":
            # Transform and clean
            records_written = _write_silver_layer(parser_name, raw_data)
        else:
            raise ValueError(f"Unknown layer: {layer}")
        
        # Update log
        log.status = "completed"
        log.records_read = records_read
        log.records_written = records_written
        log.output_path = output_path if layer == "bronze" else None
        log.completed_at = datetime.now()
        db.commit()
        
        # Publish to Telegram if enabled
        if settings.TELEGRAM_ENABLED and records_written > 0:
            _publish_to_telegram(parser_name, records_written, log.completed_at)
        
        logger.info(
            f"Ingestion job {job_id} completed: "
            f"read={records_read}, written={records_written}"
        )
        
    except Exception as e:
        logger.error(f"Ingestion job {job_id} failed: {str(e)}", exc_info=True)
        
        if log:
            log.status = "failed"
            log.error_message = str(e)
            log.completed_at = datetime.now()
            db.commit()


def _write_bronze_layer(parser_name: str, data: Any, output_path: str) -> int:
    """Write raw data to bronze layer using Spark."""
    from app.spark_services import ingest_to_bronze
    
    result = ingest_to_bronze(
        source_data=data,
        source_format="json",
        source_name=parser_name,
        table_name=f"{parser_name}_raw",
        output_path=output_path,
    )
    
    return result.get("records_written", 0)


def _write_silver_layer(parser_name: str, data: Any) -> int:
    """Transform and write to silver layer."""
    from app.spark_services import transform_to_silver
    
    result = transform_to_silver(
        bronze_table_name=f"{parser_name}_raw",
        silver_table_name=f"{parser_name}_clean",
        source_data=data,
    )
    
    return result.get("records_written", 0)


def _publish_to_telegram(parser_name: str, records_count: int, completed_at: datetime):
    """Publish ingestion summary to Telegram."""
    from app.services.telegram_service import publish_message
    
    message = (
        f"✅ Ingestion completed\n"
        f"Parser: {parser_name}\n"
        f"Records: {records_count}\n"
        f"Time: {completed_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    try:
        publish_message(message)
    except Exception as e:
        logger.error(f"Failed to publish to Telegram: {e}")


def get_available_parsers() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all available parsers.
    
    Used by API endpoint to show what parsers are available and their config.
    """
    return {
        "apk_inform": {
            "name": "APK Inform Parser",
            "description": "Scrapes agricultural data from apk-inform.com",
            "regions": settings.APK_REGIONS.split(","),
        },
        "investing_com": {
            "name": "Investing.com Parser",
            "description": "Fetches commodity prices from investing.com",
            "instruments": settings.IC_INSTRUMENTS.split(","),
        },
        "yfinance": {
            "name": "Yahoo Finance Parser",
            "description": "Collects futures prices from Yahoo Finance",
            "tickers": settings.YF_TICKERS.split(","),
        },
        "tripoli_land": {
            "name": "Tripoli Land Parser",
            "description": "Scrapes land/facility data from tripoli.land",
            "companies": settings.TL_COMPANIES.split(","),
        },
        "currency": {
            "name": "Currency Parser",
            "description": "Collects exchange rate data",
            "symbols": settings.CURR_SYMBOLS.split(","),
        },
        "graintradecomua": {
            "name": "GrainTrade.com.ua Parser",
            "description": "Scrapes grain prices from local Ukrainian site",
            "categories": "All commodity categories",
        },
    }
```

## File: `app/routers/ingestion_router.py` (Simplified)

```python
"""
Simplified Ingestion Router

Much simpler than the enhanced version:
- No config validation layer
- No factory pattern
- Direct parser names
- Clear error messages
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.database import get_db
from app.models import IngestionLog
from app.services.ingestion_service import run_ingestion, get_available_parsers
from app.logger import logger
from app.config import settings


router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/start/{parser_name}")
def start_ingestion(
    parser_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start an ingestion job for a specific parser.
    
    Supported parsers:
    - apk_inform
    - investing_com
    - yfinance
    - tripoli_land
    - currency
    - graintradecomua
    
    Example: POST /ingestion/start/yfinance
    """
    # Validate parser name
    available = get_available_parsers()
    if parser_name not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown parser: {parser_name}. Available: {', '.join(available.keys())}",
        )
    
    # Create job ID
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    
    # Create job log
    log = IngestionLog(
        job_id=job_id,
        parser_name=parser_name,
        status="started",
        layer="bronze",
        started_at=datetime.now(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    logger.info(f"Created ingestion job {job_id} for parser {parser_name}")
    
    # Start background task
    background_tasks.add_task(
        run_ingestion,
        parser_name=parser_name,
        job_id=job_id,
        db=db,
        layer="bronze",
    )
    
    return {
        "job_id": job_id,
        "parser_name": parser_name,
        "status": "started",
        "created_at": log.created_at,
    }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get status of an ingestion job."""
    log = db.query(IngestionLog).filter(IngestionLog.job_id == job_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": log.job_id,
        "parser_name": log.parser_name,
        "status": log.status,
        "records_read": log.records_read,
        "records_written": log.records_written,
        "error_message": log.error_message,
        "started_at": log.started_at,
        "completed_at": log.completed_at,
    }


@router.get("/parsers")
def list_available_parsers():
    """Get list of available parsers and their configuration."""
    return get_available_parsers()


@router.get("/jobs")
def list_jobs(
    parser_name: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    List ingestion jobs with optional filtering.
    
    Query parameters:
    - parser_name: Filter by parser name
    - status: Filter by status (started, running, completed, failed)
    - skip: Skip first N results
    - limit: Return maximum N results
    """
    query = db.query(IngestionLog)
    
    if parser_name:
        query = query.filter(IngestionLog.parser_name == parser_name)
    
    if status:
        query = query.filter(IngestionLog.status == status)
    
    jobs = query.order_by(IngestionLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "job_id": job.job_id,
            "parser_name": job.parser_name,
            "status": job.status,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
        }
        for job in jobs
    ]
```

## File: `app/config.py` (Simplified env vars section)

Add these to your .env file:

```bash
# === APK Inform Parser ===
APK_REGIONS=Kyiv,Kharkiv,Odesa
APK_UPLOAD_STORAGE=true
APK_STORAGE_TYPE=local

# === Investing.com Parser ===
IC_INSTRUMENTS=WHEAT,CORN,SOY
IC_START_DATE=2023-01-01
IC_END_DATE=
IC_RETRY_ATTEMPTS=3

# === Yahoo Finance Parser ===
YF_TICKERS=CBOT_ZWZ21,CBOT_ZWH22,CBOT_ZYH22
YF_PERIOD=1y
YF_INTERVAL=daily

# === Tripoli Land Parser ===
TL_COMPANIES=company1,company2
TL_BASE_URL=https://tripoli.land
TL_STORAGE_TYPE=local
TL_OUTPUT_FORMAT=json

# === Currency Parser ===
CURR_SYMBOLS=USD,EUR,GBP
CURR_INTERVALS=1h,4h,1d

# === GrainTrade.com.ua Parser ===
GT_BASE_URL=https://graintradecomua.com
GT_API_KEY=your_api_key
GT_TIMEOUT=30

# === Telegram ===
TELEGRAM_ENABLED=true
TELEGRAM_TOKEN=your_token
TELEGRAM_CHANNEL_ID=your_channel_id
```

---

## Why This Is Better

| Aspect | Factory Pattern | Simplified |
|--------|---|---|
| Lines of code | 700+ | 200 |
| Time to understand | 30 mins | 5 mins |
| Time to modify config | Change .env + restart | Change .env + restart (same) |
| Time to add new parser | Update factory + validator + tests | Add to get_parser_instance() |
| Debugging | Follow factory registry → validation → instantiation | Direct function call |
| Errors are | "Config validation failed" | "Cannot find ticker NONEXISTENT" (clear) |
| Testing | Mock factory, validator | Mock parser directly |

---

## Implementation Checklist

- [ ] Delete `app/services/parser_factory.py`
- [ ] Delete `app/services/config_validator.py`
- [ ] Delete `app/routers/ingestion_router_enhanced.py`
- [ ] Delete all 11 documentation files
- [ ] Create `app/services/ingestion_service.py` (use code above)
- [ ] Update `app/routers/ingestion_router.py` (use code above)
- [ ] Update `app/config.py` with simplified env vars
- [ ] Create new `README.md` (see next section)
- [ ] Test with one parser
- [ ] Test all 6 parsers
- [ ] Deploy

