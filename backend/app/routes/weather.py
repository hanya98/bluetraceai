"""
routes/weather.py
=================
GET /api/v1/weather/current
Endpoint for querying current/historical ocean wind data.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query

from app.external.weather_client import WeatherClient

router = APIRouter(tags=["Weather"])


@router.get("/weather/current")
async def get_ocean_weather(
    lat: float = Query(19.05, ge=-90.0, le=90.0),
    lon: float = Query(72.85, ge=-180.0, le=180.0),
):
    """
    Get ocean wind speed (m/s) and wind direction (degrees) for given location.
    """
    client = WeatherClient()
    data = await client.get_wind_data(lat=lat, lon=lon)
    return data
