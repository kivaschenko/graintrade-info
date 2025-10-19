"""
Agrotender Parser - Ukrainian grain prices from Agrotender.com.ua
Fetches current trader prices for various commodities
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, Dict, List
import re

logger = logging.getLogger(__name__)

# Agrotender URLs
BASE_URL = "https://agrotender.com.ua"
TRADERS_BASE = f"{BASE_URL}/traders/region_ukraine"

# Commodity mapping with their Agrotender URLs
COMMODITIES = {
    "wheat_2": {
        "name": "Пшениця 2 кл.",
        "url": f"{TRADERS_BASE}/pshenica_2_kl?viewmod=tbl",
        "standard_name": "wheat",
        "grade": "2 клас",
    },
    "wheat_3": {
        "name": "Пшениця 3 кл.",
        "url": f"{TRADERS_BASE}/pshenica_3_kl?viewmod=tbl",
        "standard_name": "wheat",
        "grade": "3 клас",
    },
    "corn": {
        "name": "Кукурудза",
        "url": f"{TRADERS_BASE}/kukuruza?viewmod=tbl",
        "standard_name": "corn",
        "grade": None,
    },
    "soybeans": {
        "name": "Соя",
        "url": f"{TRADERS_BASE}/soya?viewmod=tbl",
        "standard_name": "soybeans",
        "grade": None,
    },
    "sunflower": {
        "name": "Соняшник",
        "url": f"{TRADERS_BASE}/podsolnechnik?viewmod=tbl",
        "standard_name": "sunflower",
        "grade": None,
    },
    "rapeseed": {
        "name": "Ріпак",
        "url": f"{TRADERS_BASE}/raps?viewmod=tbl",
        "standard_name": "rapeseed",
        "grade": None,
    },
    "barley": {
        "name": "Ячмінь",
        "url": f"{TRADERS_BASE}/yachmen?viewmod=tbl",
        "standard_name": "barley",
        "grade": None,
    },
}


class AgrotenderParser:
    """Parser for Agrotender.com.ua Ukrainian grain trader prices"""

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
                "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7,ru;q=0.6",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page from Agrotender

        Args:
            url: Page URL to fetch

        Returns:
            HTML content as string or None if failed
        """
        try:
            logger.info(f"Fetching {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def parse_price(self, price_str: str) -> Optional[float]:
        """
        Parse price string to float

        Args:
            price_str: Price string (e.g., "10 500", "9,800")

        Returns:
            Price as float or None
        """
        if not price_str:
            return None

        try:
            # Remove non-numeric characters except comma and dot
            cleaned = re.sub(r"[^\d,.]", "", price_str.strip())
            # Replace comma with dot
            cleaned = cleaned.replace(",", ".")
            # Remove spaces
            cleaned = cleaned.replace(" ", "")

            if not cleaned:
                return None

            return float(cleaned)
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse price '{price_str}': {e}")
            return None

    def extract_commodity_prices(self, html: str, commodity_key: str) -> List[Dict]:
        """
        Extract price data from commodity page HTML

        Args:
            html: HTML content
            commodity_key: Commodity identifier key

        Returns:
            List of price dictionaries
        """
        prices = []

        try:
            soup = BeautifulSoup(html, "html.parser")
            commodity_info = COMMODITIES[commodity_key]

            # Find all price rows in the table
            # Agrotender uses table structure for prices
            rows = soup.find_all("tr")

            for row in rows:
                cells = row.find_all("td")

                if len(cells) < 3:
                    continue

                try:
                    # Extract data from cells
                    # Typical structure: [price, date, location, company]
                    cell_texts = [cell.get_text(strip=True) for cell in cells]

                    # Look for price (usually first cell or contains digits)
                    price_value = None
                    company = None
                    location = None
                    date_str = None

                    for i, text in enumerate(cell_texts):
                        # Price detection (contains only digits, spaces, commas)
                        if re.search(r"\d+[\s,]?\d*", text) and not any(
                            char.isalpha() for char in text
                        ):
                            if price_value is None:
                                price_value = self.parse_price(text)

                        # Company detection (link with company name)
                        if i < len(cells):
                            company_link = cells[i].find(
                                "a", href=re.compile(r"/kompanii/")
                            )
                            if company_link:
                                company = company_link.get_text(strip=True)

                        # Location detection (contains "обл" or "МП")
                        if "обл" in text or "МП" in text or "Київ" in text:
                            location = text

                        # Date detection (contains "Жов", "Вер", etc.)
                        if any(
                            month in text
                            for month in [
                                "Жов",
                                "Вер",
                                "Сер",
                                "Лип",
                                "Чер",
                                "Тра",
                                "Кві",
                                "Бер",
                                "Лют",
                                "Січ",
                                "Лис",
                                "Гру",
                            ]
                        ):
                            date_str = text

                    if price_value and price_value > 100:  # Sanity check
                        price_record = {
                            "commodity": commodity_info["standard_name"],
                            "commodity_ua": commodity_info["name"],
                            "grade": commodity_info["grade"],
                            "price_uah_per_ton": price_value,
                            "company": company or "Unknown",
                            "location": location or "Unknown",
                            "date_str": date_str or datetime.now().strftime("%d %b"),
                            "source": "Agrotender",
                            "date": datetime.now().strftime("%Y-%m-%d"),
                        }
                        prices.append(price_record)

                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue

            logger.info(f"Extracted {len(prices)} prices for {commodity_info['name']}")

        except Exception as e:
            logger.error(f"Error extracting prices for {commodity_key}: {e}")

        return prices

    def get_max_price_simple(self, html: str) -> Optional[float]:
        """
        Extract maximum price from the page summary
        Agrotender shows "максимальна ціна" on the page

        Args:
            html: HTML content

        Returns:
            Maximum price as float or None
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Look for text containing "макс. ціна" or "максимальна ціна"
            max_price_text = soup.find(text=re.compile(r"макс.*ціна", re.IGNORECASE))

            if max_price_text:
                # Find the next number
                parent = max_price_text.parent
                if parent:
                    price_match = re.search(r"(\d+[\s,]?\d*)", parent.get_text())
                    if price_match:
                        return self.parse_price(price_match.group(1))

            return None

        except Exception as e:
            logger.debug(f"Error extracting max price: {e}")
            return None

    def fetch_commodity_prices(self, commodity_key: str) -> pd.DataFrame:
        """
        Fetch prices for a specific commodity

        Args:
            commodity_key: Commodity identifier

        Returns:
            DataFrame with price data
        """
        commodity_info = COMMODITIES.get(commodity_key)

        if not commodity_info:
            logger.error(f"Unknown commodity: {commodity_key}")
            return pd.DataFrame()

        html = self.fetch_page(commodity_info["url"])

        if not html:
            logger.warning(f"No HTML for {commodity_info['name']}")
            return pd.DataFrame()

        prices = self.extract_commodity_prices(html, commodity_key)

        if not prices:
            # Try to get at least the max price
            max_price = self.get_max_price_simple(html)
            if max_price:
                prices = [
                    {
                        "commodity": commodity_info["standard_name"],
                        "commodity_ua": commodity_info["name"],
                        "grade": commodity_info["grade"],
                        "price_uah_per_ton": max_price,
                        "company": "Various (max price)",
                        "location": "Ukraine",
                        "date_str": datetime.now().strftime("%d %b"),
                        "source": "Agrotender",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                    }
                ]

        return pd.DataFrame(prices)

    def fetch_all_prices(self) -> pd.DataFrame:
        """
        Fetch prices for all supported commodities

        Returns:
            DataFrame with all commodity prices
        """
        all_prices = []

        for commodity_key in COMMODITIES.keys():
            logger.info(f"Fetching prices for {COMMODITIES[commodity_key]['name']}")
            df = self.fetch_commodity_prices(commodity_key)

            if not df.empty:
                all_prices.append(df)

        if not all_prices:
            logger.warning("No prices fetched from Agrotender")
            return pd.DataFrame()

        combined = pd.concat(all_prices, ignore_index=True)
        logger.info(f"Total prices fetched: {len(combined)}")

        return combined

    def get_max_prices_summary(self) -> pd.DataFrame:
        """
        Get maximum price for each commodity
        Useful for daily reports

        Returns:
            DataFrame with max prices per commodity
        """
        df_all = self.fetch_all_prices()

        if df_all.empty:
            return pd.DataFrame()

        # Group by commodity and get max price
        max_prices = (
            df_all.groupby(["commodity", "commodity_ua", "grade"])
            .agg(
                {
                    "price_uah_per_ton": "max",
                    "company": "first",
                    "location": "first",
                    "source": "first",
                    "date": "first",
                }
            )
            .reset_index()
        )

        return max_prices


def fetch_agrotender_prices() -> Optional[pd.DataFrame]:
    """
    Convenience function to fetch Agrotender prices

    Returns:
        DataFrame with prices or None
    """
    try:
        parser = AgrotenderParser()
        df = parser.get_max_prices_summary()
        return df if not df.empty else None
    except Exception as e:
        logger.error(f"Failed to fetch Agrotender prices: {e}")
        return None


if __name__ == "__main__":
    # Test the parser
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("Testing Agrotender parser...")
    print("=" * 60)

    parser = AgrotenderParser()

    # Test individual commodity
    print("\n1. Testing wheat 2nd class prices...")
    df_wheat = parser.fetch_commodity_prices("wheat_2")
    if not df_wheat.empty:
        print(f"✅ Fetched {len(df_wheat)} wheat prices")
        print("\nSample data:")
        print(df_wheat.head().to_string(index=False))
    else:
        print("❌ No wheat prices fetched")

    # Test max prices summary
    print("\n2. Testing max prices summary...")
    df_max = parser.get_max_prices_summary()
    if not df_max.empty:
        print(f"✅ Fetched max prices for {len(df_max)} commodities")
        print("\nMax prices:")
        print(df_max.to_string(index=False))
    else:
        print("❌ No max prices fetched")

    print("\n" + "=" * 60)
    print("Test complete!")
