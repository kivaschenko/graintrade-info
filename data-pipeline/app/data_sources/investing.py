"""Investing.com historical market data client."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import investpy
import pandas as pd

from app.logger import logger

_DATE_FMT = "%d/%m/%Y"


class InvestingDataSourceError(RuntimeError):
    """Raised when Investing.com data cannot be retrieved."""


def _format_date(value: datetime) -> str:
    return value.strftime(_DATE_FMT)


def fetch_investing_history(
    instrument_cfg: Dict[str, Any],
    start_date: datetime,
    end_date: datetime,
) -> pd.DataFrame:
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
