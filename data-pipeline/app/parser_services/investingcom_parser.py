from datetime import datetime, timezone
import os
from typing import Any, Dict, List
from pathlib import Path

import investpy
import pandas as pd

from app.parser_services.base_parser import BaseParser
from app.logger import logger
from app.storage_services import HetznerStorageService

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TIMESTAMP = ' '.join(datetime.now(timezone.utc).isoformat().split('.')[0].split('T'))
LOCAL_RESULT_DIR = BASE_DIR / "parsers_results" / "graintradecomua"
os.makedirs(LOCAL_RESULT_DIR, exist_ok=True)
RESULT_PATH = LOCAL_RESULT_DIR / f"investingcom_data_{TIMESTAMP.replace(':', '-').replace(' ', '_')}.csv"

class InvestingDataSourceError(RuntimeError):
    """Raised when Investing.com data cannot be retrieved."""

def _format_date(value: datetime) -> str:
    return value.strftime("%d/%m/%Y")

class InvestingComParser(BaseParser):
    def __init__(self, instrument_cfg: Dict[str, Any], start_date: datetime, end_date: datetime):
        self.instrument_cfg = instrument_cfg
        self.start_date = start_date
        self.end_date = end_date
        self.storage_service = HetznerStorageService()

    def parse(self) -> pd.DataFrame:
        try:
            df = fetch_investing_history(
                instrument_cfg=self.instrument_cfg,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            logger.info(f"Fetched {len(df)} records from Investing.com")
            return df
        except Exception as e:
            logger.error(f"Error fetching data from Investing.com: {e}")
            return pd.DataFrame()
        
    def save_results(self, results: pd.DataFrame, filepath: str = RESULT_PATH, file_ext: str = "csv", 
                     storage_type: str = "hetzner") -> None:
        if results.empty:
            logger.warning("No results to save.")
            return 
        if storage_type == "hetzner":
            logger.info("Saving results to Hetzner Storage")

            temp_filepath = f"/tmp/{os.path.basename(filepath)}"

            results.to_csv(temp_filepath, index=False, encoding='utf-8')
            
            self.storage_service.upload_file(file_path=temp_filepath, object_name=os.path.basename(filepath))
            os.remove(temp_filepath)
            logger.info(f"InvestingCom data uploaded to Hetzner: {filepath}")
        elif storage_type == "local":
            logger.info("Saving results locally.")
            results.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"InvestingCom data saved locally: {filepath}")
        else:
            logger.error(f"Unsupported storage type: {storage_type}")
            raise ValueError(f"Unsupported storage type: {storage_type}")


def fetch_investing_history(instrument_cfg: Dict[str, Any], start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Fetch Investing.com historical candles for the configured instrument."""
    instrument_type = instrument_cfg.get("type", "index").lower()
    symbol = instrument_cfg.get("symbol")
    if not symbol:
        raise InvestingDataSourceError("Investing instrument requires a 'symbol'")

    params: Dict[str, Any] = {
        "from_date": _format_date(start_date),
        "to_date": _format_date(end_date),
        "order": "ascending",
    }

    try:
        if instrument_type == "index":
            country = instrument_cfg.get("country", "world")
            frame = investpy.indices.get_index_historical_data(
                index=symbol,
                country=country,
                **params,
            )
        elif instrument_type == "commodity":
            frame = investpy.commodities.get_commodity_historical_data(
                commodity=symbol,
                **params,
            )
        elif instrument_type == "etf":
            country = instrument_cfg.get("country", "united states")
            frame = investpy.etfs.get_etf_historical_data(
                etf=symbol,
                country=country,
                **params,
            )
        elif instrument_type == "currency_cross":
            frame = investpy.currency_crosses.get_currency_cross_historical_data(
                currency_cross=symbol,
                **params,
            )
        else:
            raise InvestingDataSourceError(
                f"Unsupported Investing.com instrument type: {instrument_type}"
            )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Failed to download Investing.com history for %s (%s): %s",
            symbol,
            instrument_type,
            exc,
        )
        raise InvestingDataSourceError(str(exc)) from exc

    frame = frame.reset_index().rename(columns={"Date": "date"})
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    frame["ticker"] = instrument_cfg.get("symbol", symbol)
    return frame

if __name__ == "__main__":
    # Example usage
    instrument_cfg = {
        "type": "commodity",
        "symbol": "Gold",
    }
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)

    parser = InvestingComParser(instrument_cfg, start_date, end_date)
    data_frame = parser.parse()
    if not data_frame.empty:
        print(data_frame.head())
        parser.save_results(data_frame, storage_type="hetzner")
        parser.save_results(data_frame, storage_type="local")
    else:
        print("No data fetched from Investing.com.")