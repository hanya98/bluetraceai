"""
schemas/attribution.py
======================
Attribution API schemas (Model 3 input and output).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import Coordinates


class SpillRecordInput(BaseModel):
    spill_id: str
    timestamp_utc: datetime
    centroid: Tuple_Lat_Lon
    area_km2: Optional[float] = None
    polygon: Optional[List[List[float]]] = None
    drift_direction_deg: Optional[float] = Field(default=None, ge=0.0, le=360.0)
    drift_speed_kmh: Optional[float] = None
    oil_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    detection_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class Tuple_Lat_Lon(BaseModel):
    lat: float
    lon: float

    def to_tuple(self) -> tuple[float, float]:
        return (self.lat, self.lon)


class AISPingInput(BaseModel):
    vessel_id: str
    timestamp_utc: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed_knots: Optional[float] = None
    heading_deg: Optional[float] = Field(default=None, ge=0.0, le=360.0)


class EnvironmentalInput(BaseModel):
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = Field(default=None, ge=0.0, le=360.0)
    source: str = "open-meteo"
    is_modelled: bool = True


class AttributionRequest(BaseModel):
    spill: SpillRecordInput
    ais_records: List[AISPingInput]
    environment: Optional[EnvironmentalInput] = None


class RankedVessel(BaseModel):
    vessel_id: str
    rank: int
    candidate_priority_score: float
    explanation: str


class AttributionResponse(BaseModel):
    spill_id: str
    mode_used: str
    ranked_vessels: List[RankedVessel]
    preprocessing_report: Optional[Dict[str, Any]] = None
