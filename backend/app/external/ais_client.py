"""
external/ais_client.py
======================
Global Fishing Watch / AIS events API client.
Provides candidate vessel trajectory data near a given spill centroid.
Uses real GFW API when key is configured, or cached sample AIS dataset when offline.
NO synthetic/random fallback generation is used.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
SAMPLE_AIS_FILE = ASSETS_DIR / "sample_ais_records.json"


class AISClient:
    """Async AIS client for retrieving candidate vessel trajectories."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.GFW_API_KEY
        self.base_url = (self.settings.GFW_BASE_URL or "https://gateway.api.globalfishingwatch.org/v3").rstrip("/")

    def _make_circle_polygon(
        self, lat: float, lon: float, radius_km: float = 50.0, points: int = 36
    ) -> Dict[str, Any]:
        """Generate GeoJSON Polygon geometry representing a circle around (lat, lon)."""
        lat_delta = radius_km / 111.0
        cos_lat = math.cos(math.radians(lat))
        lon_delta = radius_km / (111.0 * cos_lat) if cos_lat != 0 else radius_km / 111.0
        coords = []
        for i in range(points + 1):
            angle = 2 * math.pi * i / points
            p_lat = lat + lat_delta * math.sin(angle)
            p_lon = lon + lon_delta * math.cos(angle)
            coords.append([round(p_lon, 6), round(p_lat, 6)])
        return {
            "type": "Polygon",
            "coordinates": [coords],
        }

    async def get_nearby_vessels(
        self,
        lat: float,
        lon: float,
        spill_time: datetime,
        radius_km: float = 50.0,
        lookback_hours: int = 12,
    ) -> List[Dict[str, Any]]:
        """
        Fetch AIS observations near spill location.
        Queries Global Fishing Watch API via POST /v3/events if GFW_API_KEY is configured.
        Otherwise falls back to cached sample AIS dataset.
        """
        if self.api_key:
            try:
                if spill_time.tzinfo is None:
                    spill_time = spill_time.replace(tzinfo=timezone.utc)
                else:
                    spill_time = spill_time.astimezone(timezone.utc)

                start_dt = spill_time - timedelta(hours=lookback_hours)
                end_dt = spill_time + timedelta(days=1)

                start_date = start_dt.strftime("%Y-%m-%d")
                end_date = end_dt.strftime("%Y-%m-%d")

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }

                params = {
                    "limit": 100,
                    "offset": 0,
                }

                geometry = self._make_circle_polygon(lat, lon, radius_km=radius_km)

                body = {
                    "datasets": [
                        "public-global-loitering-events:latest",
                        "public-global-encounters-events:latest",
                        "public-global-gaps-events:latest",
                        "public-global-port-visits-events:latest",
                        "public-global-fishing-events:latest",
                    ],
                    "startDate": start_date,
                    "endDate": end_date,
                    "geometry": geometry,
                }

                async with httpx.AsyncClient(timeout=self.settings.HTTP_TIMEOUT) as client:
                    resp = await client.post(
                        f"{self.base_url}/events",
                        headers=headers,
                        params=params,
                        json=body,
                    )
                    if resp.status_code in (200, 201):
                        events = resp.json().get("entries", [])
                        parsed = self._parse_gfw_events(events)
                        if parsed:
                            logger.info(f"Retrieved {len(parsed)} events from GFW API.")
                            return parsed
                        else:
                            logger.warning(
                                "GFW AIS API returned 0 entries for region. Falling back to cached sample AIS data."
                            )
                    else:
                        logger.error(
                            "GFW AIS API HTTP %s\n%s",
                            resp.status_code,
                            resp.text,
                        )
            except Exception as e:
                logger.warning(f"GFW AIS API call failed ({e}). Using cached sample AIS data.")

        # Fallback to loading static cached sample AIS dataset
        return self._load_cached_sample_ais()

    def _load_cached_sample_ais(self) -> List[Dict[str, Any]]:
        """Loads static cached sample AIS records from file system."""
        if SAMPLE_AIS_FILE.exists():
            try:
                with open(SAMPLE_AIS_FILE, "r", encoding="utf-8") as f:
                    records = json.load(f)
                logger.info(f"Loaded {len(records)} cached sample AIS records from {SAMPLE_AIS_FILE.name}.")
                return records
            except Exception as e:
                logger.error(f"Failed to read sample AIS file: {e}")

        logger.warning("No sample AIS file available; returning empty AIS record list.")
        return []

    def _parse_gfw_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        records = []
        for ev in events:
            vessel = ev.get("vessel", {})
            pos = ev.get("position", {})
            vessel_id = vessel.get("id") or vessel.get("ssvid") or vessel.get("mmsi") or ev.get("id") or "UNKNOWN"
            timestamp = ev.get("start") or ev.get("timestamp") or ev.get("end") or datetime.now(timezone.utc).isoformat()
            lat_val = pos.get("lat") if "lat" in pos else pos.get("latitude", 0.0)
            lon_val = pos.get("lon") if "lon" in pos else pos.get("longitude", 0.0)
            speed = ev.get("vesselSpeedKnots") or ev.get("speedKnots") or ev.get("speed") or 8.0
            heading = ev.get("vesselHeadingDeg") or ev.get("headingDeg") or ev.get("heading") or 0.0

            records.append({
                "vessel_id": str(vessel_id),
                "timestamp_utc": str(timestamp),
                "latitude": float(lat_val or 0.0),
                "longitude": float(lon_val or 0.0),
                "speed_knots": float(speed or 8.0),
                "heading_deg": float(heading or 0.0),
            })
        return records

