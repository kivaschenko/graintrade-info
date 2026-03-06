"""
Ingestion Service - Simplified orchestrator (NOT a factory pattern)

This replaces the factory pattern approach with direct, simple parser usage.
Configuration comes from environment variables, not database JSON.
"""
from typing import Dict, Any
from datetime import datetime
import uuid

from app.config import settings
from app.logger import logger
from app.models import IngestionLog
from sqlalchemy.orm import Session


# Direct parser imports - no registry, no dynamic lookup
try:
    from app.parser_services.apk_inform_parser import APKInformParser
    from app.parser_services.investingcom_parser import InvestingComParser
    from app.parser_services.yfinance_parser import YFinanceParser
    from app.parser_services.tripoli_land_parser import TripoliLandParser
    from app.parser_services.currency_parser import CurrencyParser
    from app.parser_services.graintradecomua_parser import GraintradeComuaParser
except ImportError as e:
    logger.warning(f"Not all parsers available: {e}")
    # Parsers will be imported on-demand if they fail


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
    if parser_name == "apk_inform":
        return APKInformParser(
            regions=settings.APK_REGIONS.split(",") if hasattr(settings, "APK_REGIONS") else ["Kyiv"],
            upload_to_storage=getattr(settings, "APK_UPLOAD_STORAGE", False),
            storage_type=getattr(settings, "APK_STORAGE_TYPE", "local"),
        )
    
    elif parser_name == "investing_com":
        return InvestingComParser(
            instruments=settings.IC_INSTRUMENTS.split(",") if hasattr(settings, "IC_INSTRUMENTS") else ["WHEAT"],
            start_date=getattr(settings, "IC_START_DATE", "2023-01-01"),
            end_date=getattr(settings, "IC_END_DATE", None),
            retry_attempts=getattr(settings, "IC_RETRY_ATTEMPTS", 3),
        )
    
    elif parser_name == "yfinance":
        return YFinanceParser(
            tickers=settings.YF_TICKERS.split(",") if hasattr(settings, "YF_TICKERS") else ["CBOT_ZWZ21"],
            period=getattr(settings, "YF_PERIOD", "1y"),
            interval=getattr(settings, "YF_INTERVAL", "daily"),
            progress=settings.ENV == "development",
        )
    
    elif parser_name == "tripoli_land":
        return TripoliLandParser(
            companies=settings.TL_COMPANIES.split(",") if hasattr(settings, "TL_COMPANIES") else ["company1"],
            base_url=getattr(settings, "TL_BASE_URL", "https://tripoli.land"),
            storage_type=getattr(settings, "TL_STORAGE_TYPE", "local"),
            output_format=getattr(settings, "TL_OUTPUT_FORMAT", "json"),
        )
    
    elif parser_name == "currency":
        return CurrencyParser(
            symbols=settings.CURR_SYMBOLS.split(",") if hasattr(settings, "CURR_SYMBOLS") else ["USD", "EUR"],
            intervals=settings.CURR_INTERVALS.split(",") if hasattr(settings, "CURR_INTERVALS") else ["1h"],
        )
    
    elif parser_name == "graintradecomua":
        return GraintradeComuaParser(
            base_url=getattr(settings, "GT_BASE_URL", "https://graintradecomua.com"),
            api_key=getattr(settings, "GT_API_KEY", ""),
            timeout=getattr(settings, "GT_TIMEOUT", 30),
        )
    
    else:
        raise ValueError(
            f"Unknown parser: {parser_name}. "
            f"Available: apk_inform, investing_com, yfinance, tripoli_land, currency, graintradecomua"
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
        if getattr(settings, "TELEGRAM_ENABLED", False) and records_written > 0:
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
    try:
        from app.spark_services import ingest_to_bronze
        
        result = ingest_to_bronze(
            source_data=data,
            source_format="json",
            source_name=parser_name,
            table_name=f"{parser_name}_raw",
            output_path=output_path,
        )
        
        return result.get("records_written", 0)
    except Exception as e:
        logger.error(f"Failed to write bronze layer: {e}")
        return 0


def _write_silver_layer(parser_name: str, data: Any) -> int:
    """Transform and write to silver layer."""
    try:
        from app.spark_services import transform_to_silver
        
        result = transform_to_silver(
            bronze_table_name=f"{parser_name}_raw",
            silver_table_name=f"{parser_name}_clean",
            source_data=data,
        )
        
        return result.get("records_written", 0)
    except Exception as e:
        logger.error(f"Failed to write silver layer: {e}")
        return 0


def _publish_to_telegram(parser_name: str, records_count: int, completed_at: datetime):
    """Publish ingestion summary to Telegram."""
    try:
        from app.services.telegram_service import publish_message
        
        message = (
            f"✅ Ingestion completed\n"
            f"Parser: {parser_name}\n"
            f"Records: {records_count}\n"
            f"Time: {completed_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        publish_message(message)
    except Exception as e:
        logger.warning(f"Failed to publish to Telegram: {e}")


def get_available_parsers() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all available parsers.
    
    Used by API endpoint to show what parsers are available and their config.
    """
    return {
        "apk_inform": {
            "name": "APK Inform Parser",
            "description": "Scrapes agricultural data from apk-inform.com",
            "regions": getattr(settings, "APK_REGIONS", "Kyiv").split(","),
        },
        "investing_com": {
            "name": "Investing.com Parser",
            "description": "Fetches commodity prices from investing.com",
            "instruments": getattr(settings, "IC_INSTRUMENTS", "WHEAT").split(","),
        },
        "yfinance": {
            "name": "Yahoo Finance Parser",
            "description": "Collects futures prices from Yahoo Finance",
            "tickers": getattr(settings, "YF_TICKERS", "CBOT_ZWZ21").split(","),
        },
        "tripoli_land": {
            "name": "Tripoli Land Parser",
            "description": "Scrapes land/facility data from tripoli.land",
            "companies": getattr(settings, "TL_COMPANIES", "company1").split(","),
        },
        "currency": {
            "name": "Currency Parser",
            "description": "Collects exchange rate data",
            "symbols": getattr(settings, "CURR_SYMBOLS", "USD,EUR").split(","),
        },
        "graintradecomua": {
            "name": "GrainTrade.com.ua Parser",
            "description": "Scrapes grain prices from local Ukrainian site",
            "categories": "All commodity categories",
        },
    }
