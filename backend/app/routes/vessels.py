"""
routes/vessels.py
=================
GET /api/v1/vessels/nearby
Endpoint for querying nearby candidate AIS vessel tracks.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query

from app.external.ais_client import AISClient

router = APIRouter(tags=["Vessels"])


@router.get("/vessels/nearby")
async def get_nearby_vessels(
    lat: float = Query(19.05, ge=-90.0, le=90.0),
    lon: float = Query(72.85, ge=-180.0, le=180.0),
    radius_km: float = Query(50.0, ge=5.0, le=200.0),
    lookback_hours: int = Query(12, ge=1, le=72),
):
    """
    Get AIS tracks for candidate vessels near given lat/lon coordinates.
    """
    now = datetime.now(timezone.utc)
    client = AISClient()
    vessels = await client.get_nearby_vessels(
        lat=lat,
        lon=lon,
        spill_time=now,
        radius_km=radius_km,
        lookback_hours=lookback_hours,
    )

    return {
        "count": len(vessels),
        "center": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
        "vessels": vessels,
    }
