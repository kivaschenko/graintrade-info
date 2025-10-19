#!/usr/bin/env python3
"""
Test script for Agrotender parser and integration
"""

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agrotender_parser import AgrotenderParser, fetch_agrotender_prices

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def test_agrotender_parser():
    """Test Agrotender parser functionality"""
    print("\n" + "=" * 60)
    print("Testing Agrotender Parser")
    print("=" * 60)

    parser = AgrotenderParser()

    # Test 1: Fetch single commodity
    print("\n1. Testing single commodity (wheat 2nd class)...")
    df_wheat = parser.fetch_commodity_prices("wheat_2")

    if not df_wheat.empty:
        print(f"✅ Successfully fetched {len(df_wheat)} wheat prices")
        print("\nSample data (first 5 rows):")
        print(df_wheat.head().to_string(index=False))

        # Check required columns
        required_cols = ["commodity", "price_uah_per_ton", "company", "source"]
        missing_cols = [col for col in required_cols if col not in df_wheat.columns]

        if missing_cols:
            print(f"⚠️  Missing columns: {missing_cols}")
        else:
            print("✅ All required columns present")

        # Check price ranges
        max_price = df_wheat["price_uah_per_ton"].max()
        min_price = df_wheat["price_uah_per_ton"].min()
        avg_price = df_wheat["price_uah_per_ton"].mean()

        print("\nPrice statistics:")
        print(f"  Maximum: {max_price:.0f} ₴/т")
        print(f"  Minimum: {min_price:.0f} ₴/т")
        print(f"  Average: {avg_price:.0f} ₴/т")

        if max_price < 1000 or max_price > 50000:
            print(f"⚠️  Maximum price seems unusual: {max_price} ₴/т")

    else:
        print("❌ Failed to fetch wheat prices")
        return False

    # Test 2: Test price parsing
    print("\n2. Testing price parsing...")
    test_prices = [
        ("10 500", 10500.0),
        ("9,800", 9800.0),
        ("8500", 8500.0),
        ("10 300", 10300.0),
        ("invalid", None),
    ]

    all_passed = True
    for price_str, expected in test_prices:
        result = parser.parse_price(price_str)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{price_str}' -> {result} (expected: {expected})")
        if result != expected:
            all_passed = False

    if all_passed:
        print("✅ All price parsing tests passed")
    else:
        print("⚠️  Some price parsing tests failed")

    # Test 3: Fetch all commodities
    print("\n3. Testing all commodities fetch...")
    df_all = parser.fetch_all_prices()

    if not df_all.empty:
        print(f"✅ Fetched {len(df_all)} total prices")

        # Show commodity breakdown
        commodity_counts = df_all.groupby("commodity").size()
        print("\nPrices per commodity:")
        for commodity, count in commodity_counts.items():
            print(f"  {commodity}: {count} prices")
    else:
        print("❌ Failed to fetch all prices")
        return False

    # Test 4: Max prices summary
    print("\n4. Testing max prices summary...")
    df_max = parser.get_max_prices_summary()

    if not df_max.empty:
        print(f"✅ Got max prices for {len(df_max)} commodities")
        print("\nMax prices summary:")
        print(
            df_max[["commodity_ua", "price_uah_per_ton", "company"]].to_string(
                index=False
            )
        )
    else:
        print("❌ Failed to get max prices summary")
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

        print("\n1. Testing load_ukrainian_prices() with Agrotender...")
        df_ukr = load_ukrainian_prices()

        if df_ukr is not None and not df_ukr.empty:
            print(f"✅ Loaded {len(df_ukr)} Ukrainian prices")
            print("\nSample data:")
            print(df_ukr.head().to_string(index=False))

            # Check source
            source = df_ukr.iloc[0].get("source", "Unknown")
            print(f"\nData source: {source}")

            if "Agrotender" in source:
                print("✅ Successfully using Agrotender as primary source")
            else:
                print("ℹ️  Using alternative source (Agrotender may have failed)")
        else:
            print("⚠️  No Ukrainian prices loaded")

        print("\n2. Testing format_telegram_daily_report() with Agrotender data...")

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

        print("\n✅ Successfully generated report with Agrotender prices")
        print("\n" + "-" * 60)
        print("Report Preview (first 600 chars):")
        print("-" * 60)
        print(message[:600] + "...")

        # Check if Ukrainian prices with trader info are in the message
        if "🇺🇦" in message and "Українські ціни" in message:
            print("\n✅ Ukrainian prices section found in report")

            if "трейдери" in message.lower():
                print("✅ Trader-specific information included")

            if "Agrotender" in message:
                print("✅ Agrotender source mentioned")
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


def test_convenience_function():
    """Test convenience function"""
    print("\n" + "=" * 60)
    print("Testing Convenience Function")
    print("=" * 60)

    print("\nTesting fetch_agrotender_prices()...")
    df = fetch_agrotender_prices()

    if df is not None and not df.empty:
        print(f"✅ Successfully fetched {len(df)} prices")
        print("\nData preview:")
        print(df.to_string(index=False))
        return True
    else:
        print("❌ Failed to fetch prices via convenience function")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Agrotender Parser Test Suite")
    print("=" * 60)

    results = {
        "Parser Tests": test_agrotender_parser(),
        "Convenience Function": test_convenience_function(),
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
