"""
schemas/detection.py
====================
Detection API schemas (Model 1 output).
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import BoundingBox, Coordinates, GeoJSONPolygon


class DetectionRequestParams(BaseModel):
    lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    threshold: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)
    pixel_scale_km: Optional[float] = Field(default=0.01, description="KM per pixel scale")


class DetectionResponse(BaseModel):
    spill_detected: bool
    confidence: float
    centroid: Optional[Coordinates] = None
    area_km2: Optional[float] = None
    bounding_box: Optional[BoundingBox] = None
    mask_polygon: Optional[GeoJSONPolygon] = None
    pixel_mask_shape: List[int] = Field(default_factory=lambda: [256, 256])
    model: str = "AttentionUNet"
    threshold_used: float = 0.5
