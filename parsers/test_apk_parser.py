#!/usr/bin/env python3
"""
Test script for APK-Inform parser and integration with yfinance_parser
"""

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apk_inform_parser import fetch_ukrainian_prices, APKInformParser

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def test_apk_parser():
    """Test APK-Inform parser functionality"""
    print("\n" + "=" * 60)
    print("Testing APK-Inform Parser")
    print("=" * 60)

    # Test 1: Fetch prices
    print("\n1. Fetching Ukrainian prices...")
    df = fetch_ukrainian_prices()

    if df is not None and not df.empty:
        print(f"✅ Successfully fetched {len(df)} prices")
        print("\nPrice data:")
        print(df.to_string(index=False))

        # Check required columns
        required_cols = ["commodity", "price_uah_per_ton", "basis", "source"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"⚠️  Missing columns: {missing_cols}")
        else:
            print("✅ All required columns present")

        # Check price ranges (sanity check)
        for _, row in df.iterrows():
            price = row["price_uah_per_ton"]
            commodity = row["commodity"]
            if price < 1000 or price > 50000:
                print(f"⚠️  Price for {commodity} seems unusual: {price} ₴/т")

    else:
        print("❌ Failed to fetch prices")
        return False

    # Test 2: Test parser class methods
    print("\n2. Testing parser class methods...")
    parser = APKInformParser()

    # Test price parsing
    test_prices = [
        ("8500", 8500.0),
        ("8500-8700", 8600.0),
        ("8 500,00", 8500.0),
        ("7200.50", 7200.50),
        ("invalid", None),
    ]

    print("\nPrice parsing tests:")
    all_passed = True
    for price_str, expected in test_prices:
        result = parser.parse_price_value(price_str)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{price_str}' -> {result} (expected: {expected})")
        if result != expected:
            all_passed = False

    if all_passed:
        print("✅ All price parsing tests passed")
    else:
        print("⚠️  Some price parsing tests failed")

    # Test 3: Test fallback prices
    print("\n3. Testing fallback prices...")
    df_fallback = parser.get_fallback_prices()

    if not df_fallback.empty:
        print(f"✅ Fallback prices available ({len(df_fallback)} commodities)")
        print("\nFallback prices:")
        print(
            df_fallback[["commodity", "price_uah_per_ton", "basis"]].to_string(
                index=False
            )
        )
    else:
        print("❌ No fallback prices available")
        return False

    return True


def test_integration():
    """Test integration with main parser"""
    print("\n" + "=" * 60)
    print("Testing Integration with Main Parser")
    print("=" * 60)

    try:
        from yfinance_parser import (
            load_ukrainian_prices,
            format_telegram_daily_report,
            fetch_usd_to_uah,
            get_commodity_prices,
        )

        print("\n1. Testing load_ukrainian_prices()...")
        df_ukr = load_ukrainian_prices()

        if df_ukr is not None and not df_ukr.empty:
            print(f"✅ Loaded {len(df_ukr)} Ukrainian prices")
        else:
            print("⚠️  No Ukrainian prices loaded (this is OK if scraping failed)")

        print("\n2. Testing format_telegram_daily_report() with Ukrainian prices...")

        # Get exchange rate
        usd_to_uah = fetch_usd_to_uah()
        print(f"USD to UAH rate: {usd_to_uah:.2f}")

        # Get commodity prices
        df_commodities = get_commodity_prices(usd_to_uah)

        if df_commodities.empty:
            print("❌ Failed to get commodity prices")
            return False

        # Format report
        message = format_telegram_daily_report(df_commodities, usd_to_uah, df_ukr)

        print("\n✅ Successfully generated report with Ukrainian prices")
        print("\n" + "-" * 60)
        print("Report Preview (first 500 chars):")
        print("-" * 60)
        print(message[:500] + "...")

        # Check if Ukrainian prices are in the message
        if "🇺🇦" in message and "Українські ціни" in message:
            print("\n✅ Ukrainian prices section found in report")
        else:
            print("\n⚠️  Ukrainian prices section not found in report")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("APK-Inform Parser Test Suite")
    print("=" * 60)

    results = {
        "Parser Tests": test_apk_parser(),
        "Integration Tests": test_integration(),
    }

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
