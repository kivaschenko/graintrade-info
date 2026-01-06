"""Utility helpers for currency rates and conversions."""
from __future__ import annotations

import requests

from app.logger import logger

COURSE_UAH_USD_FALLBACK = 41.0


def fetch_usd_to_uah() -> float:
    """Get current USD/UAH exchange rate from multiple public sources."""
    # Source 1: exchangerate-api.com
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "rates" in data and "UAH" in data["rates"]:
                rate = float(data["rates"]["UAH"])
                logger.info("USD/UAH rate from exchangerate-api.com: %s", rate)
                return rate
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to get rate from exchangerate-api.com: %s", exc)

    # Source 2: National Bank of Ukraine
    try:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                rate = float(data[0]["rate"])
                logger.info("USD/UAH rate from NBU: %s", rate)
                return rate
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to get rate from NBU: %s", exc)

    logger.warning(
        "All exchange rate sources failed, using fallback: %s",
        COURSE_UAH_USD_FALLBACK,
    )
    return COURSE_UAH_USD_FALLBACK
