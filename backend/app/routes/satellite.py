"""
routes/satellite.py
===================
GET /api/v1/satellite/search
Endpoint for searching Sentinel-1 GRD SAR scenes in Copernicus STAC catalog.
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Query

from app.external.sentinel_client import SentinelClient

router = APIRouter(tags=["Satellite"])


@router.get("/satellite/search")
async def search_satellite_scenes(
    min_lon: float = Query(72.0, ge=-180.0, le=180.0),
    min_lat: float = Query(18.5, ge=-90.0, le=90.0),
    max_lon: float = Query(73.5, ge=-180.0, le=180.0),
    max_lat: float = Query(19.5, ge=-90.0, le=90.0),
    start_date: str = Query("2026-09-01T00:00:00Z"),
    end_date: str = Query("2026-09-12T23:59:59Z"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Search Sentinel-1 GRD SAR scenes in Copernicus STAC catalog.
    """
    bbox = [min_lon, min_lat, max_lon, max_lat]
    client = SentinelClient()
    scenes = await client.search_scenes(bbox=bbox, start_date=start_date, end_date=end_date, limit=limit)
    return {"count": len(scenes), "bbox": bbox, "scenes": scenes}
