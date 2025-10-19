import yfinance as yf
from transformers import pipeline
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

COURSE_UAH_USD_FALLBACK = 41.7537  # fallback value

# Extended commodities with more grain trading related tickers
# Using ETFs and spot prices when futures are not available
COMMODITIES = {
    "Wheat ETF": {
        "ticker": "WEAT",  # Teucrium Wheat Fund ETF
        "unit": "share",
        "factor": 1.0,
        "description": "Пшениця (ETF)",
    },
    "Corn ETF": {
        "ticker": "CORN",
        "unit": "share",
        "factor": 1.0,
        "description": "Кукурудза (ETF)",
    },
    "Soybeans ETF": {
        "ticker": "SOYB",
        "unit": "share",
        "factor": 1.0,
        "description": "Соя (ETF)",
    },
    "Agricultural Basket": {
        "ticker": "DBA",
        "unit": "share",
        "factor": 1.0,
        "description": "Аграрний кошик (ETF)",
    },
    "Sugar ETF": {
        "ticker": "CANE",
        "unit": "share",
        "factor": 1.0,
        "description": "Цукор (ETF)",
    },
    "Coffee ETF": {
        "ticker": "JO",
        "unit": "share",
        "factor": 1.0,
        "description": "Кава (ETF)",
    },
    # Add some major agricultural companies
    "ADM": {
        "ticker": "ADM",
        "unit": "share",
        "factor": 1.0,
        "description": "Archer-Daniels-Midland (аграрна компанія)",
    },
    "Bunge": {
        "ticker": "BG",
        "unit": "share",
        "factor": 1.0,
        "description": "Bunge Limited (аграрна компанія)",
    },
    "Tyson Foods": {
        "ticker": "TSN",
        "unit": "share",
        "factor": 1.0,
        "description": "Tyson Foods (м'ясна компанія)",
    },
    # Alternative tickers
    "Mosaic (Fertilizer)": {
        "ticker": "MOS",
        "unit": "share",
        "factor": 1.0,
        "description": "Mosaic Company (добрива)",
    },
}

# HuggingFace summarizer
try:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except Exception as e:
    logger.warning(f"Failed to load summarizer model: {e}")
    summarizer = None


def get_price(symbol, name):
    """Get current price for a commodity ticker"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty:
            logger.warning(f"No data available for {symbol}")
            return f"{name}: Дані недоступні"
        last_price = data["Close"].iloc[-1]
        return f"{name}: {last_price:.2f} USD"
    except Exception as e:
        logger.error(f"Error getting price for {symbol}: {e}")
        return f"{name}: Помилка отримання ціни"


def make_summary(prices_text):
    """Create summary using AI model if available"""
    if summarizer is None:
        return "Автоматичне резюме недоступне"

    try:
        # Ensure the text is not too long for the model
        if len(prices_text) > 1000:
            prices_text = prices_text[:1000]

        summary = summarizer(prices_text, max_length=60, min_length=20, do_sample=False)
        return summary[0]["summary_text"]
    except Exception as e:
        logger.error(f"Error creating summary: {e}")
        return "Помилка створення резюме"


def get_usd_to_uah_rate():
    """Get current USD/UAH exchange rate from free API sources"""
    # Try multiple free sources

    # Source 1: Free exchangerate API (no key required)
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "rates" in data and "UAH" in data["rates"]:
                rate = data["rates"]["UAH"]
                logger.info(f"USD/UAH rate from exchangerate-api.com: {rate}")
                return float(rate)
    except Exception as e:
        logger.warning(f"Failed to get rate from exchangerate-api.com: {e}")

    # Source 2: Free fixer.io (free tier, no key for USD base)
    try:
        url = "https://api.fixer.io/latest?base=USD&symbols=UAH"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "rates" in data and "UAH" in data["rates"]:
                rate = data["rates"]["UAH"]
                logger.info(f"USD/UAH rate from fixer.io: {rate}")
                return float(rate)
    except Exception as e:
        logger.warning(f"Failed to get rate from fixer.io: {e}")

    # Source 3: NBU (National Bank of Ukraine) - official rate
    try:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                rate = data[0]["rate"]
                logger.info(f"USD/UAH rate from NBU: {rate}")
                return float(rate)
    except Exception as e:
        logger.warning(f"Failed to get rate from NBU: {e}")

    # Fallback to static value
    logger.warning(
        f"All exchange rate sources failed, using fallback: {COURSE_UAH_USD_FALLBACK}"
    )
    return COURSE_UAH_USD_FALLBACK


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
