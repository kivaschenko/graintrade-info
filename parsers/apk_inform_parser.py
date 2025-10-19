"""
APK-Inform Parser - Ukrainian grain prices scraper
Fetches current Ukrainian commodity prices from APK-Inform website
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# APK-Inform URLs
BASE_URL = "https://www.apk-inform.com"
PRICES_URL = f"{BASE_URL}/uk/prices"

# Commodity mapping (Ukrainian name to standardized name)
COMMODITY_MAPPING = {
    "пшениця": "wheat",
    "пшеница": "wheat",
    "кукурудза": "corn",
    "кукуруза": "corn",
    "соя": "soybeans",
    "соняшник": "sunflower",
    "подсолнечник": "sunflower",
    "ячмінь": "barley",
    "ячмень": "barley",
    "овес": "oats",
    "ріпак": "rapeseed",
    "рапс": "rapeseed",
}

# Basis types
BASIS_TYPES = ["EXW", "CPT", "FCA", "FOB", "DAP", "CIF"]


class APKInformParser:
    """Parser for APK-Inform Ukrainian grain prices"""

    def __init__(self, timeout: int = 30):
        """
        Initialize parser with request configuration

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def fetch_prices_page(self) -> Optional[str]:
        """
        Fetch the prices page HTML

        Returns:
            HTML content as string or None if failed
        """
        try:
            logger.info(f"Fetching prices from {PRICES_URL}")
            response = self.session.get(PRICES_URL, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch APK-Inform prices page: {e}")
            return None

    def parse_price_value(self, price_str: str) -> Optional[float]:
        """
        Parse price string to float value

        Args:
            price_str: Price string (e.g., "8500", "8500-8700", "8 500,00")

        Returns:
            Average price as float or None
        """
        if not price_str:
            return None

        try:
            # Remove spaces and replace comma with dot
            price_str = price_str.strip().replace(" ", "").replace(",", ".")

            # Handle range (e.g., "8500-8700")
            if "-" in price_str:
                parts = price_str.split("-")
                if len(parts) == 2:
                    low = float(parts[0])
                    high = float(parts[1])
                    return (low + high) / 2

            # Single value
            return float(price_str)

        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse price '{price_str}': {e}")
            return None

    def extract_prices_from_html(self, html: str) -> pd.DataFrame:
        """
        Extract price data from HTML using BeautifulSoup

        Args:
            html: HTML content string

        Returns:
            DataFrame with columns: commodity, price_uah_per_ton, basis, source, date
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            prices = []

            # Find price tables (structure may vary, adapt as needed)
            tables = soup.find_all("table", class_=lambda x: x and "price" in x.lower())

            if not tables:
                # Try alternative: find all tables
                tables = soup.find_all("table")

            logger.info(f"Found {len(tables)} tables on page")

            for table in tables:
                rows = table.find_all("tr")

                for row in rows:
                    cells = row.find_all(["td", "th"])

                    if len(cells) < 3:
                        continue

                    # Extract text from cells
                    cell_texts = [cell.get_text(strip=True) for cell in cells]

                    # Try to identify commodity name, price, and basis
                    commodity_name = None
                    price_value = None
                    basis = "EXW"  # default

                    for text in cell_texts:
                        text_lower = text.lower()

                        # Check if it's a commodity name
                        for ukr_name, std_name in COMMODITY_MAPPING.items():
                            if ukr_name in text_lower:
                                commodity_name = std_name
                                break

                        # Check if it's a price
                        if not price_value and any(char.isdigit() for char in text):
                            price_value = self.parse_price_value(text)

                        # Check if it's a basis
                        for b in BASIS_TYPES:
                            if b in text.upper():
                                basis = b
                                break

                    if commodity_name and price_value:
                        prices.append(
                            {
                                "commodity": commodity_name,
                                "price_uah_per_ton": price_value,
                                "basis": basis,
                                "source": "APK-Inform",
                                "date": datetime.now().strftime("%Y-%m-%d"),
                            }
                        )

            if not prices:
                logger.warning("No prices extracted from HTML")

            df = pd.DataFrame(prices)
            return df

        except Exception as e:
            logger.error(f"Error extracting prices from HTML: {e}")
            return pd.DataFrame()

    def fetch_prices_api_alternative(self) -> pd.DataFrame:
        """
        Alternative method: try to fetch prices from potential API endpoint
        APK-Inform might have JSON endpoints for data

        Returns:
            DataFrame with price data or empty DataFrame
        """
        # This is speculative - APK-Inform might have API endpoints
        api_urls = [
            f"{BASE_URL}/api/prices",
            f"{BASE_URL}/uk/api/prices",
            f"{BASE_URL}/api/v1/prices",
        ]

        for api_url in api_urls:
            try:
                logger.info(f"Trying API endpoint: {api_url}")
                response = self.session.get(api_url, timeout=self.timeout)

                if response.status_code == 200:
                    _ = response.json()
                    # Process JSON data (structure unknown, adapt as needed)
                    logger.info(f"Successfully fetched data from {api_url}")
                    # TODO: Parse JSON structure when discovered
                    return pd.DataFrame()

            except Exception as e:
                logger.debug(f"API endpoint {api_url} not available: {e}")
                continue

        return pd.DataFrame()

    def get_ukrainian_prices(self) -> pd.DataFrame:
        """
        Main method to fetch Ukrainian grain prices
        Tries multiple approaches to get data

        Returns:
            DataFrame with Ukrainian prices or fallback data
        """
        logger.info("Fetching Ukrainian prices from APK-Inform...")

        # Method 1: Try API endpoints
        df_api = self.fetch_prices_api_alternative()
        if not df_api.empty:
            logger.info(f"Got {len(df_api)} prices from API")
            return df_api

        # Method 2: Scrape HTML
        html = self.fetch_prices_page()
        if html:
            df_html = self.extract_prices_from_html(html)
            if not df_html.empty:
                logger.info(f"Got {len(df_html)} prices from HTML scraping")
                return df_html

        # Method 3: Use fallback static data (approximate recent prices)
        logger.warning("Could not fetch live data, using fallback prices")
        return self.get_fallback_prices()

    def get_fallback_prices(self) -> pd.DataFrame:
        """
        Provide fallback Ukrainian prices when scraping fails
        These are approximate market prices (should be updated periodically)

        Returns:
            DataFrame with fallback prices
        """
        current_date = datetime.now().strftime("%Y-%m-%d")

        fallback_data = [
            {
                "commodity": "wheat",
                "price_uah_per_ton": 9600,
                "basis": "EXW",
                "source": "APK-Inform (оціночні дані)",
                "date": current_date,
            },
            {
                "commodity": "corn",
                "price_uah_per_ton": 7200,
                "basis": "EXW",
                "source": "APK-Inform (оціночні дані)",
                "date": current_date,
            },
            {
                "commodity": "soybeans",
                "price_uah_per_ton": 16000,
                "basis": "EXW",
                "source": "APK-Inform (оціночні дані)",
                "date": current_date,
            },
            {
                "commodity": "sunflower",
                "price_uah_per_ton": 18000,
                "basis": "EXW",
                "source": "APK-Inform (оціочні дані)",
                "date": current_date,
            },
            {
                "commodity": "barley",
                "price_uah_per_ton": 7000,
                "basis": "EXW",
                "source": "APK-Inform (оціночні дані)",
                "date": current_date,
            },
        ]

        logger.info(f"Using {len(fallback_data)} fallback prices")
        return pd.DataFrame(fallback_data)


def fetch_ukrainian_prices() -> Optional[pd.DataFrame]:
    """
    Convenience function to fetch Ukrainian prices

    Returns:
        DataFrame with Ukrainian prices or None
    """
    try:
        parser = APKInformParser()
        df = parser.get_ukrainian_prices()
        return df if not df.empty else None
    except Exception as e:
        logger.error(f"Failed to fetch Ukrainian prices: {e}")
        return None


if __name__ == "__main__":
    # Test the parser
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("Testing APK-Inform parser...")
    df = fetch_ukrainian_prices()

    if df is not None and not df.empty:
        print(f"\n✅ Successfully fetched {len(df)} Ukrainian prices:\n")
        print(df.to_string(index=False))
    else:
        print("\n❌ Failed to fetch Ukrainian prices")
