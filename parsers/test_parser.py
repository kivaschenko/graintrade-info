#!/usr/bin/env python3
"""
Test script to verify commodity price parser output and RabbitMQ message format
"""

import asyncio
import json
from yfinance_draft import (
    get_commodity_prices,
    get_usd_to_uah_rate,
    format_telegram_message,
)


async def test_commodity_parser():
    """Test the commodity price parser functions"""
    print("🧪 Testing Commodity Price Parser")
    print("=" * 50)

    # Test exchange rate
    print("1. Testing USD/UAH exchange rate...")
    try:
        usd_uah_rate = get_usd_to_uah_rate()
        print(f"   ✅ USD/UAH rate: {usd_uah_rate:.2f}")
    except Exception as e:
        print(f"   ❌ Exchange rate error: {e}")
        return False

    # Test commodity prices
    print("\n2. Testing commodity price fetching...")
    try:
        commodity_df = get_commodity_prices()
        if commodity_df.empty:
            print("   ❌ No commodity data received")
            return False

        print(f"   ✅ Fetched data for {len(commodity_df)} commodities")
        print(f"   📊 Available tickers: {', '.join(commodity_df['Ticker'].tolist())}")

        # Show sample data
        print("\n   Sample data:")
        for _, row in commodity_df.head(3).iterrows():
            print(f"   - {row['Description']}: ${row['Raw Price']:.2f}")

    except Exception as e:
        print(f"   ❌ Commodity price error: {e}")
        return False

    # Test Telegram message formatting
    print("\n3. Testing Telegram message formatting...")
    try:
        telegram_message = format_telegram_message(commodity_df, usd_uah_rate)
        print("   ✅ Telegram message generated")
        print(f"   📝 Message length: {len(telegram_message)} characters")

        # Show first few lines
        lines = telegram_message.split("\n")
        print("   📋 Message preview:")
        for line in lines[:5]:
            print(f"      {line}")
        if len(lines) > 5:
            print(f"      ... and {len(lines) - 5} more lines")

    except Exception as e:
        print(f"   ❌ Message formatting error: {e}")
        return False

    # Test message structure for RabbitMQ
    print("\n4. Testing RabbitMQ message structure...")
    try:
        from datetime import datetime

        message_data = {
            "type": "commodity_prices",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "telegram_message": telegram_message,
                "usd_uah_rate": usd_uah_rate,
                "commodities": commodity_df.to_dict("records"),
            },
            "destination": "telegram_channel",
        }

        # Validate JSON serialization
        json_message = json.dumps(message_data, ensure_ascii=False, indent=2)
        print("   ✅ RabbitMQ message structure valid")
        print(f"   📦 Message size: {len(json_message)} bytes")

        # Save sample message for inspection
        with open("sample_rabbitmq_message.json", "w", encoding="utf-8") as f:
            f.write(json_message)
        print("   💾 Sample message saved to 'sample_rabbitmq_message.json'")

    except Exception as e:
        print(f"   ❌ RabbitMQ message error: {e}")
        return False

    print(f"\n🎉 All tests passed! The commodity parser is working correctly.")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_commodity_parser())
    exit(0 if success else 1)
