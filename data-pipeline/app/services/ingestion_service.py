"""
Ingestion Service - Simplified orchestrator (NOT a factory pattern)

This replaces the factory pattern approach with direct, simple parser usage.
Configuration comes from environment variables, not database JSON.
"""
from typing import Any, Callable, Dict
from datetime import datetime

import pandas as pd

from app.config import settings
from app.logger import logger
from app.models import IngestionLog
from app.utils.rates import fetch_usd_to_uah
from sqlalchemy.orm import Session


class CallableParser:
    def __init__(self, parse_func: Callable[[], Any]) -> None:
        self._parse_func = parse_func

    def parse(self) -> Any:
        return self._parse_func()


def _enabled_parser_names() -> list[str]:
    configured = [item.strip() for item in settings.ENABLED_PARSERS.split(",") if item.strip()]
    return configured or ["yfinance"]


def _build_yfinance_dataset() -> pd.DataFrame:
    from app.parser_services.yfinance_parser import get_commodity_prices

    return get_commodity_prices(fetch_usd_to_uah())


def _parser_factories() -> Dict[str, Callable[[], Any]]:
    return {
        "yfinance": lambda: CallableParser(_build_yfinance_dataset),
        "apk_inform": _create_apk_inform_parser,
        "investing_com": _create_investing_parser,
        "tripoli_land": _create_tripoli_land_parser,
        "currency": _create_currency_parser,
        "graintradecomua": _create_graintradecomua_parser,
    }


def _create_apk_inform_parser():
    from app.parser_services.apk_inform_parser import APKInformParser

    return APKInformParser(regions=getattr(settings, "APK_REGIONS", "Kyiv").split(","))


def _create_investing_parser():
    from app.parser_services.investingcom_parser import InvestingComParser

    instrument_cfg = {
        "type": getattr(settings, "IC_INSTRUMENT_TYPE", "commodity"),
        "symbol": getattr(settings, "IC_SYMBOL", "Wheat"),
        "country": getattr(settings, "IC_COUNTRY", "world"),
    }
    start_date = pd.Timestamp(getattr(settings, "IC_START_DATE", "2023-01-01")).to_pydatetime()
    end_date_raw = getattr(settings, "IC_END_DATE", None)
    end_date = pd.Timestamp(end_date_raw).to_pydatetime() if end_date_raw else datetime.utcnow()
    return InvestingComParser(
        instrument_cfg=instrument_cfg,
        start_date=start_date,
        end_date=end_date,
    )


def _create_tripoli_land_parser():
    from app.parser_services.tripoli_land_parser import TripoliLandParser

    return TripoliLandParser()


def _create_currency_parser():
    from app.parser_services.currency_parser import CurrencyParser

    return CurrencyParser()


def _create_graintradecomua_parser():
    from app.parser_services.graintradecomua_parser import GrainTradeComUaParser

    return GrainTradeComUaParser(parse_history=getattr(settings, "GT_PARSE_HISTORY", True))


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
    enabled = set(_enabled_parser_names())
    if parser_name not in enabled:
        raise ValueError(
            f"Parser '{parser_name}' is disabled. Enabled parsers: {', '.join(sorted(enabled))}"
        )

    factory = _parser_factories().get(parser_name)
    if not factory:
        raise ValueError(f"Unknown parser: {parser_name}")
    return factory()


def _count_records(raw_data: Any) -> int:
    if isinstance(raw_data, pd.DataFrame):
        return len(raw_data.index)
    if isinstance(raw_data, list):
        return len(raw_data)
    if isinstance(raw_data, dict):
        return 1
    return 0 if raw_data is None else 1


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
        
        records_read = _count_records(raw_data)
        logger.info(f"Parser {parser_name} collected {records_read} records")
        
        # Store in appropriate layer
        if layer == "bronze":
            # Store raw data in bronze layer
            output_path = f"{settings.BRONZE_LAYER_PATH}/{parser_name}_raw"
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
    available = {
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
    enabled = set(_enabled_parser_names())
    return {name: meta for name, meta in available.items() if name in enabled}
