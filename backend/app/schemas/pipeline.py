"""
schemas/pipeline.py
===================
Unified pipeline API schemas (POST /api/v1/analyze).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.attribution import RankedVessel
from app.schemas.classification import ClassificationResponse
from app.schemas.common import BoundingBox, Coordinates, GeoJSONPolygon
from app.schemas.detection import DetectionResponse


class FullAnalysisRequest(BaseModel):
    # Location/scene options
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    timestamp_utc: Optional[datetime] = Field(default_factory=datetime.utcnow)
    ais_lookback_hours: int = Field(default=12, ge=1, le=72)
    search_radius_km: float = Field(default=50.0, ge=5.0, le=200.0)
    fetch_weather: bool = True
    fetch_ais: bool = True


class FullAnalysisResponse(BaseModel):
    analysis_id: str
    timestamp_utc: datetime
    location: Coordinates
    detection: DetectionResponse
    classification: Optional[ClassificationResponse] = None
    weather: Optional[Dict[str, Any]] = None
    attribution: Optional[Dict[str, Any]] = None
    summary: str
