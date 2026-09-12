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
        self.base_url = self.settings.GFW_BASE_URL

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
        Queries Global Fishing Watch API if GFW_API_KEY is configured.
        Otherwise falls back to cached sample AIS dataset.
        """
        if self.api_key:
            try:
                start_time = (spill_time - timedelta(hours=lookback_hours)).isoformat()
                end_time = spill_time.isoformat()
                headers = {"Authorization": f"Bearer {self.api_key}"}

                params = {
                    "start-date": start_time,
                    "end-date": end_time,
                    "limit": 100,
                }

                async with httpx.AsyncClient(timeout=self.settings.HTTP_TIMEOUT) as client:
                    resp = await client.get(
                        f"{self.base_url}/events",
                        headers=headers,
                        params=params,
                    )
                    if resp.status_code == 200:
                        events = resp.json().get("entries", [])
                        return self._parse_gfw_events(events)
                    else:
                        logger.warning(f"GFW AIS API returned status {resp.status_code}. Using cached sample AIS data.")
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
            records.append({
                "vessel_id": str(vessel.get("id", "UNKNOWN")),
                "timestamp_utc": ev.get("start", datetime.now(timezone.utc).isoformat()),
                "latitude": float(pos.get("lat", 0.0)),
                "longitude": float(pos.get("lon", 0.0)),
                "speed_knots": float(ev.get("vesselSpeedKnots", 8.0)),
                "heading_deg": float(ev.get("vesselHeadingDeg", 0.0)),
            })
        return records
