#!/usr/bin/env python3
"""
Test script for geocoding service
Tests various address formats for Ukraine
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

from app.service_layer.geocoding_service import (
    geocode_address,
    reverse_geocode,
    geocode_with_fallback,
)


async def test_geocoding():
    print("🧪 Testing Nominatim Geocoding Service\n")
    print("=" * 60)

    test_addresses = [
        "Kyiv, Ukraine",
        "Київ, Україна",
        "Odesa",
        "вулиця Хрещатик, Київ",
        "Lviv, Ukraine",
        "Dnipro, Dnipropetrovsk Oblast, Ukraine",
        "Poltava",
        "Kharkiv, Ukraine",
    ]

    for i, address in enumerate(test_addresses, 1):
        print(f"\n{i}. Testing: '{address}'")
        print("-" * 60)

        try:
            result = await geocode_address(address, country="Ukraine")

            if result:
                print(f"✅ Success!")
                print(f"   Latitude:  {result['latitude']:.4f}")
                print(f"   Longitude: {result['longitude']:.4f}")
                print(f"   Country:   {result['country']}")
                print(f"   Region:    {result['region']}")
                print(f"   Display:   {result['display_name']}")
            else:
                print(f"❌ Failed: No results found")

        except Exception as e:
            print(f"❌ Error: {e}")

        # Small delay to respect rate limit
        if i < len(test_addresses):
            await asyncio.sleep(1.1)

    print("\n" + "=" * 60)
    print("\n🧪 Testing Reverse Geocoding\n")
    print("=" * 60)

    # Test reverse geocoding (Kyiv coordinates)
    print("\nTesting coordinates: 50.4501, 30.5234 (Kyiv)")
    print("-" * 60)

    try:
        result = await reverse_geocode(50.4501, 30.5234)

        if result:
            print(f"✅ Success!")
            print(f"   Country:   {result['country']}")
            print(f"   Region:    {result['region']}")
            print(f"   City:      {result['city']}")
            print(f"   Display:   {result['display_name']}")
        else:
            print(f"❌ Failed: No results found")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("\n🧪 Testing Geocoding with Fallback\n")
    print("=" * 60)

    # Test with address only
    print("\n1. With address only")
    print("-" * 60)
    lat, lon, country, region = await geocode_with_fallback(address="Kyiv, Ukraine")
    print(f"   Coordinates: {lat}, {lon}")
    print(f"   Country: {country}, Region: {region}")

    await asyncio.sleep(1.1)

    # Test with coordinates provided (should skip geocoding)
    print("\n2. With coordinates provided (should skip geocoding)")
    print("-" * 60)
    lat, lon, country, region = await geocode_with_fallback(
        latitude=50.0, longitude=30.0, country="Ukraine", region="Test Region"
    )
    print(f"   Coordinates: {lat}, {lon}")
    print(f"   Country: {country}, Region: {region}")

    await asyncio.sleep(1.1)

    # Test with country/region only
    print("\n3. With country and region only")
    print("-" * 60)
    lat, lon, country, region = await geocode_with_fallback(
        country="Ukraine", region="Lviv Oblast"
    )
    print(f"   Coordinates: {lat}, {lon}")
    print(f"   Country: {country}, Region: {region}")

    print("\n" + "=" * 60)
    print("\n✅ All tests completed!")
    print("\nNote: Some addresses may not be found if too generic.")
    print("This is normal and items will still be created (without map display).")


if __name__ == "__main__":
    print("\n🚀 Starting Geocoding Service Tests\n")
    asyncio.run(test_geocoding())
