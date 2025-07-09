import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas import GeoSearchRequest, DirectionsRequest
from ..models.subscription_model import increment_map_views, increment_geo_search_count, increment_navigation_count

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRES_IN")
MAP_VIEW_LIMIT = os.getenv("MAP_VIEW_LIMIT")
MAPBOX_TOKEN = os.getenv("MAPBOX_SECRET_TOKEN")
MAPBOX_API_BASE_URL = "https://api.mapbox.com"


router = APIRouter(tags=["map"])


@router.post("/mapbox/map-view")
async def increment_map_view(user_id: int):
    """Increment map_views count for the user."""
    map_views = await increment_map_views(user_id=user_id)
    return {"message": "Map view counted", "map_views": map_views}


@router.post("/mapbox/geo-search")
async def proxy_geo_search(request: GeoSearchRequest, user_id: int):
    """Proxies Mapbox Geocoding API and increments geo_search_count."""
    geo_search_count = await increment_geo_search_count(
        user_id=user_id, column_name="geo_search_count"
    )

    async with httpx.AsyncClient() as client:
        mapbox_url = (
            f"{MAPBOX_API_BASE_URL}/geocoding/v5/mapbox.places/{request.query}.json"
        )
        params = {"token": MAPBOX_TOKEN}
        response = await client.get(mapbox_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        mapbox_results = response.json()

    return {
        "message": "Geo search successful",
        "geo_search_count": geo_search_count,
        "features": mapbox_results.get("features", [])  # Return Mapbox results
    }


@router.post("/mapbox/directions")
async def proxy_directions(request: DirectionsRequest, user_id: int):
    """Proxies Mapbox Directions API and increments navigation_count."""
    navigation_count = await increment_navigation_count(user_id)
    async with httpx.AsyncClient() as client:
        coordinates_str = f"{request.origin[0]},{request.origin[1]};{request.destination[0]},{request.destination[1]}"
        mapbox_url = f"{MAPBOX_API_BASE_URL}/directions/v5/mapbox/driving/{coordinates_str}"
        params = {
            "alternatives": "true",
            "geometries": "geojson",
            "language": "en",
            "overview": "full",
            "steps": "true",
            "access_token": MAPBOX_TOKEN
        }
        response = await client.get(mapbox_url, params=params)
        response.raise_for_status()
        mapbox_results = response.json()
        # Assuming want to return the first route found
        route = mapbox_results["routes"][0] if mapbox_results and "routes" in mapbox_results else None
        return {
            "message": "Directions successful",
            "navigation_count": navigation_count,
            "route": route,
        }















