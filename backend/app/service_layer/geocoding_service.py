"""
Geocoding service using Nominatim (OpenStreetMap) API
Free and unlimited geocoding service for converting addresses to coordinates
"""

import asyncio
import logging
from typing import Optional, Dict, Tuple
import aiohttp
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting: Nominatim requires max 1 request per second
_last_request_time = 0
_rate_limit_delay = 1.0  # seconds


async def _wait_for_rate_limit():
    """Ensure we don't exceed Nominatim rate limit (1 req/sec)"""
    global _last_request_time
    current_time = asyncio.get_event_loop().time()
    time_since_last = current_time - _last_request_time

    if time_since_last < _rate_limit_delay:
        await asyncio.sleep(_rate_limit_delay - time_since_last)

    _last_request_time = asyncio.get_event_loop().time()


async def geocode_address(
    address: str, country: Optional[str] = None
) -> Optional[Dict]:
    """
    Convert address to coordinates using Nominatim API

    Args:
        address: Full text address (e.g., "Kyiv, Ukraine" or "вулиця Хрещатик, Київ")
        country: Optional country filter to improve accuracy

    Returns:
        Dict with: {
            'latitude': float,
            'longitude': float,
            'country': str,
            'region': str,
            'display_name': str
        }
        or None if geocoding failed
    """
    await _wait_for_rate_limit()

    # Build query
    query = address
    if country:
        query = f"{address}, {country}"

    encoded_query = quote(query)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&addressdetails=1&limit=1"

    headers = {
        "User-Agent": "GrainTrade.info Agricultural Trading Platform (contact@graintrade.info)"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    if not data or len(data) == 0:
                        logger.warning(f"No results found for address: {address}")
                        return None

                    result = data[0]
                    address_details = result.get("address", {})
                    print(f"Geocoding result for address '{address}': {result}")
                    return {
                        "latitude": float(result["lat"]),
                        "longitude": float(result["lon"]),
                        "country": address_details.get("country", ""),
                        "region": address_details.get("state")
                        or address_details.get("region", ""),
                        "city": address_details.get("city")
                        or address_details.get("town")
                        or address_details.get("village", ""),
                        "display_name": result.get("display_name", address),
                        "address_type": result.get("type", "unknown"),
                    }
                else:
                    logger.error(f"Nominatim API error: {response.status}")
                    return None

    except asyncio.TimeoutError:
        logger.error(f"Timeout while geocoding address: {address}")
        return None
    except Exception as e:
        logger.error(f"Error geocoding address '{address}': {e}")
        return None


async def reverse_geocode(latitude: float, longitude: float) -> Optional[Dict]:
    """
    Convert coordinates to address using Nominatim API

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Dict with address information or None if failed
    """
    await _wait_for_rate_limit()

    url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json&addressdetails=1"

    headers = {
        "User-Agent": "GrainTrade.info Agricultural Trading Platform (contact@graintrade.info)"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    address_details = data.get("address", {})

                    return {
                        "country": address_details.get("country", ""),
                        "region": address_details.get("state")
                        or address_details.get("region", ""),
                        "city": address_details.get("city")
                        or address_details.get("town")
                        or address_details.get("village", ""),
                        "display_name": data.get("display_name", ""),
                        "address_type": data.get("type", "unknown"),
                    }
                else:
                    logger.error(f"Nominatim reverse geocode error: {response.status}")
                    return None

    except asyncio.TimeoutError:
        logger.error(f"Timeout while reverse geocoding: {latitude}, {longitude}")
        return None
    except Exception as e:
        logger.error(f"Error reverse geocoding ({latitude}, {longitude}): {e}")
        return None


async def geocode_with_fallback(
    address: Optional[str] = None,
    country: Optional[str] = None,
    region: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> Tuple[Optional[float], Optional[float], str, str]:
    """
    Flexible geocoding with multiple fallback strategies

    Priority:
    1. If coordinates provided - use them (reverse geocode to get address details)
    2. If full address provided - geocode it
    3. If only country/region - try to geocode them

    Returns:
        Tuple: (latitude, longitude, country, region)
    """

    # Strategy 1: Coordinates already provided
    if latitude is not None and longitude is not None:
        # Optionally reverse geocode to get/verify country and region
        if not country or not region:
            reverse_result = await reverse_geocode(latitude, longitude)
            if reverse_result:
                country = country or reverse_result.get("country", "")
                region = region or reverse_result.get("region", "")

        return latitude, longitude, country or "", region or ""

    # Strategy 2: Full address provided
    if address:
        # Try geocoding with country hint if available
        result = await geocode_address(address, country)
        if result:
            return (
                result["latitude"],
                result["longitude"],
                result.get("country", country or ""),
                result.get("region", region or ""),
            )

    # Strategy 3: Try country + region
    if country:
        search_address = country
        if region:
            search_address = f"{region}, {country}"

        result = await geocode_address(search_address)
        if result:
            return (
                result["latitude"],
                result["longitude"],
                result.get("country", country),
                result.get("region", region or ""),
            )

    # No geocoding possible
    logger.warning("Unable to geocode: insufficient location data")
    return None, None, country or "", region or ""


# Example address formats that work well:
"""
Good examples:
- "Kyiv, Ukraine"
- "вулиця Хрещатик, Київ, Україна"
- "Odesa, Odesa Oblast, Ukraine"
- "Lviv"
- "49.8397, 24.0297" (coordinates as string)
- "Дніпро, Україна"
- "Poltava region, Ukraine"
"""
