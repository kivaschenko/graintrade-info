import yfinance as yf
from datetime import datetime
import pandas as pd
import requests
import json
import asyncio
import aio_pika
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional, Tuple

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "message.events")

COURSE_UAH_USD_FALLBACK = 41.0  # fallback value

# --- COMPREHENSIVE COMMODITIES CONFIG ---
# Includes futures contracts (quoted in cents), ETFs, and company stocks
COMMODITIES = {
    # === FUTURES CONTRACTS (CBOT) - quoted in cents ===
    "Wheat Futures": {
        "ticker": "ZW=F",
        "unit": "bushel",
        "kg_per_unit": 27.2155,
        "cents_per_dollar": 100,
        "category": "futures",
        "description": "Пшениця (ф'ючерс CBOT)",
    },
    "Corn Futures": {
        "ticker": "ZC=F",
        "unit": "bushel",
        "kg_per_unit": 25.4012,
        "cents_per_dollar": 100,
        "category": "futures",
        "description": "Кукурудза (ф'ючерс CBOT)",
    },
    "Soybeans Futures": {
        "ticker": "ZS=F",
        "unit": "bushel",
        "kg_per_unit": 27.2155,
        "cents_per_dollar": 100,
        "category": "futures",
        "description": "Соя (ф'ючерс CBOT)",
    },
    "Oats Futures": {
        "ticker": "ZO=F",
        "unit": "bushel",
        "kg_per_unit": 14.5150,
        "cents_per_dollar": 100,
        "category": "futures",
        "description": "Овес (ф'ючерс CBOT)",
    },
    "Rough Rice Futures": {
        "ticker": "ZR=F",
        "unit": "cwt",
        "kg_per_unit": 45.359237,
        "cents_per_dollar": 100,
        "category": "futures",
        "description": "Рис (ф'ючерс CBOT)",
    },
    # === ETFs (Exchange Traded Funds) - quoted in dollars ===
    "Wheat ETF": {
        "ticker": "WEAT",
        "unit": "share",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "etf",
        "description": "Пшениця (ETF)",
    },
    "Corn ETF": {
        "ticker": "CORN",
        "unit": "share",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "etf",
        "description": "Кукурудза (ETF)",
    },
    "Soybeans ETF": {
        "ticker": "SOYB",
        "unit": "share",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "etf",
        "description": "Соя (ETF)",
    },
    "Agricultural Basket": {
        "ticker": "DBA",
        "unit": "share",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "etf",
        "description": "Аграрний кошик (ETF)",
    },
    "Sugar ETF": {
        "ticker": "CANE",
        "unit": "share",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "etf",
        "description": "Цукор (ETF)",
    },
    "Coffee ETF": {
        "ticker": "JO",
        "unit": "share",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "etf",
        "description": "Кава (ETF)",
    },
    # === COMPANIES ===
    "ADM": {
        "ticker": "ADM",
        "unit": "share",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "company",
        "description": "Archer-Daniels-Midland (аграрна компанія)",
    },
    "Bunge": {
        "ticker": "BG",
        "unit": "share",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "company",
        "description": "Bunge Limited (аграрна компанія)",
    },
    "Tyson Foods": {
        "ticker": "TSN",
        "unit": "share",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "company",
        "description": "Tyson Foods (м'ясна компанія)",
    },
    "Mosaic (Fertilizer)": {
        "ticker": "MOS",
        "unit": "share",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "company",
        "description": "Mosaic Company (добрива)",
    },
}

# Optional: local CSV path with Ukrainian prices
UKR_PRICES_CSV = Path("ukraine_prices.csv")


# --- HELPER FUNCTIONS ---


def fetch_usd_to_uah() -> float:
    """Get current USD/UAH exchange rate from multiple sources"""

    # Source 1: exchangerate-api.com
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "rates" in data and "UAH" in data["rates"]:
                rate = float(data["rates"]["UAH"])
                logger.info(f"USD/UAH rate from exchangerate-api.com: {rate}")
                return rate
    except Exception as e:
        logger.warning(f"Failed to get rate from exchangerate-api.com: {e}")

    # Source 2: NBU (National Bank of Ukraine) - official rate
    try:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                rate = float(data[0]["rate"])
                logger.info(f"USD/UAH rate from NBU: {rate}")
                return rate
    except Exception as e:
        logger.warning(f"Failed to get rate from NBU: {e}")

    # Fallback to static value
    logger.warning(
        f"All exchange rate sources failed, using fallback: {COURSE_UAH_USD_FALLBACK}"
    )
    return COURSE_UAH_USD_FALLBACK


def fetch_price_yf(ticker: str):
    """
    Fetch last close price from Yahoo Finance.
    Handles anomalies in rice futures and other data inconsistencies.
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")  # Get more days to detect anomalies
        if hist.empty:
            logger.warning(f"No data available for {ticker}")
            return None

        # Special handling for rough rice futures (ZR=F) due to pricing anomalies
        if ticker == "ZR=F" and len(hist) > 1:
            recent_prices = hist["Close"].tail(5)
            latest_price = recent_prices.iloc[-1]
            # If latest price is dramatically different from recent average, use previous value
            if len(recent_prices) > 1:
                avg_previous = recent_prices.iloc[:-1].mean()
                if (
                    abs(latest_price - avg_previous) / avg_previous > 0.5
                ):  # 50% difference threshold
                    logger.warning(
                        f"{ticker} latest price {latest_price:.2f} differs significantly "
                        f"from recent average {avg_previous:.2f}, using previous price"
                    )
                    return float(recent_prices.iloc[-2])

        return float(hist["Close"].iloc[-1])
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return None


def convert_to_usd_per_ton(price: float, kg_per_unit: float):
    """
    Convert price quoted per unit (e.g., per bushel or per cwt) into USD/tonne.

    Args:
        price: Price in USD per unit
        kg_per_unit: How many kg in 1 quoted unit

    Returns:
        Price in USD per metric ton (1000 kg), or None if conversion not possible
    """
    if price is None or kg_per_unit is None:
        return None
    # 1 tonne = 1000 kg, factor = 1000 / kg_per_unit
    factor = 1000.0 / kg_per_unit
    return price * factor


def get_commodity_prices():
    """Get current commodity prices and convert to USD/ton and UAH/ton"""
    usd_to_uah = get_usd_to_uah_rate()
    data = []

    for name, info in COMMODITIES.items():
        try:
            ticker = yf.Ticker(info["ticker"])
            history = ticker.history(period="1d")

            if history.empty:
                logger.warning(f"No data available for {name} ({info['ticker']})")
                continue

            price = history["Close"].iloc[-1]

            # For shares, we'll use the share price directly
            if info["unit"] == "share":
                usd_per_share = price
                uah_per_share = usd_per_share * usd_to_uah

                data.append(
                    {
                        "Commodity": name,
                        "Ticker": info["ticker"],
                        "Raw Price": round(price, 2),
                        "Unit": info["unit"],
                        "USD/share": round(usd_per_share, 2),
                        "UAH/share": round(uah_per_share, 2),
                        "Description": info["description"],
                    }
                )
            else:
                # Calculate price per ton for traditional commodities
                if info["unit"] == "tonne":
                    usd_per_ton = price  # Already in per ton
                elif info["unit"] == "bushel":
                    usd_per_ton = price / info["factor"]  # Convert from bushel to ton
                elif info["unit"] == "cwt":
                    usd_per_ton = price / info["factor"]  # Convert from cwt to ton
                elif info["unit"] == "lb":
                    usd_per_ton = price / info["factor"]  # Convert from lb to ton
                elif info["unit"] == "mt":
                    usd_per_ton = price  # Already in metric ton
                else:
                    usd_per_ton = price * info["factor"]

                uah_per_ton = usd_per_ton * usd_to_uah

                data.append(
                    {
                        "Commodity": name,
                        "Ticker": info["ticker"],
                        "Raw Price": round(price, 2),
                        "Unit": info["unit"],
                        "USD/ton": round(usd_per_ton, 2),
                        "UAH/ton": round(uah_per_ton, 2),
                        "Description": info["description"],
                    }
                )

        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            continue

    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(by="Commodity").reset_index(drop=True)
    return df


async def publish_to_rabbitmq(message_data: dict):
    """Publish message to RabbitMQ for notifications service"""
    try:
        connection = await aio_pika.connect_robust(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            login=RABBITMQ_USER,
            password=RABBITMQ_PASS,
            virtualhost=RABBITMQ_VHOST,
        )

        channel = await connection.channel()

        # Declare queue for message events
        await channel.declare_queue("message.events", durable=True)

        # Publish message
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message_data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key="message.events",
        )

        logger.info(f"Message published to RabbitMQ: {message_data['type']}")
        await connection.close()

    except Exception as e:
        logger.error(f"Failed to publish to RabbitMQ: {e}")


def format_telegram_message(commodity_df: pd.DataFrame, usd_to_uah_rate: float):
    """Format data as Telegram message"""
    current_date = datetime.today().strftime("%d.%m.%Y")

    # Header
    message = f"📊 **Аграрний ринок** ({current_date})\n"
    message += f"💱 Курс USD/UAH: {usd_to_uah_rate:.2f}\n\n"

    # Group by categories
    etfs = [
        "Wheat ETF",
        "Corn ETF",
        "Soybeans ETF",
        "Agricultural Basket",
        "Sugar ETF",
        "Coffee ETF",
    ]
    companies = ["ADM", "Bunge", "Tyson Foods", "Mosaic (Fertilizer)"]

    def add_category(title: str, items: list, emoji: str):
        nonlocal message
        category_items = commodity_df[commodity_df["Commodity"].isin(items)]
        if not category_items.empty:
            message += f"{emoji} **{title}:**\n"
            for _, row in category_items.iterrows():
                change_emoji = "📈" if row["Raw Price"] > 0 else "📉"
                if row["Unit"] == "share":
                    # For shares, show price in USD and UAH equivalent
                    uah_price = row["Raw Price"] * usd_to_uah_rate
                    message += f"{change_emoji} {row['Description']}: "
                    message += f"${row['Raw Price']:.2f} ({uah_price:.0f} ₴)\n"
                else:
                    # For commodities per ton
                    message += f"{change_emoji} {row['Description']}: "
                    message += f"{row['Raw Price']:.2f} USD/{row['Unit']} "
                    message += f"({row.get('UAH/ton', 0):.0f} ₴/т)\n"
            message += "\n"

    add_category("Товарні ETF", etfs, "🌾")
    add_category("Аграрні компанії", companies, "🏭")

    # Footer
    message += "📝 *Дані отримані з фондових бірж у реальному часі*\n"
    message += f"🕐 Оновлено: {datetime.now().strftime('%H:%M')}"

    return message


async def main():
    """Main function to get prices and send to RabbitMQ"""
    try:
        logger.info("Starting commodity price parsing...")

        # Get commodity prices
        commodity_df = get_commodity_prices()

        if commodity_df.empty:
            logger.warning("No commodity data available")
            return

        # Get exchange rate
        usd_to_uah_rate = get_usd_to_uah_rate()

        # Format Telegram message
        telegram_message = format_telegram_message(commodity_df, usd_to_uah_rate)

        # Prepare message for RabbitMQ
        message_data = {
            "type": "commodity_prices",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "telegram_message": telegram_message,
                "usd_uah_rate": usd_to_uah_rate,
                "commodities": commodity_df.to_dict("records"),
            },
            "destination": "telegram_channel",
        }

        # Publish to RabbitMQ
        await publish_to_rabbitmq(message_data)

        # Print for testing
        print("Telegram message preview:")
        print(telegram_message)
        print("\nData sent to RabbitMQ successfully!")

    except Exception as e:
        logger.error(f"Error in main function: {e}")


# Legacy function for backward compatibility
def get_legacy_prices():
    """Legacy function for simple price getting (for testing)"""
    try:
        prices = []
        basic_commodities = ["ZW=F", "ZC=F", "ZS=F"]
        commodity_names = ["Пшениця (CBOT)", "Кукурудза (CBOT)", "Соя (CBOT)"]

        for ticker, name in zip(basic_commodities, commodity_names):
            price_str = get_price(ticker, name)
            prices.append(price_str)

        prices_text = "\n".join(prices)
        summary = make_summary(" ".join(prices))

        post = (
            f"📊 Щоденний огляд цін на біржі ({datetime.today().date()}):\n\n"
            + prices_text
            + "\n\n"
            + f"📝 {summary}"
        )

        return post

    except Exception as e:
        logger.error(f"Error in legacy function: {e}")
        return f"Помилка отримання даних: {e}"


if __name__ == "__main__":
    # Run the main async function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Script failed: {e}")

        # Fallback to legacy function if main fails
        print("\nFalling back to legacy function:")
        legacy_post = get_legacy_prices()
        print(legacy_post)
