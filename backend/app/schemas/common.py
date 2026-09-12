"""
schemas/common.py
=================
Common geospatial and metadata schemas (Pydantic v2).
"""
from __future__ import annotations

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")


class BoundingBox(BaseModel):
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


class GeoJSONPolygon(BaseModel):
    type: str = Field(default="Polygon", Literal=True)
    coordinates: List[List[List[float]]]  # [[[lon, lat], [lon, lat], ...]]
