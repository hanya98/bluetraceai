"""
schemas/classification.py
=========================
Classification & Object Detection API schemas (Model 2 YOLO11n output).
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class YOLODetectionBox(BaseModel):
    box: List[float] = Field(..., description="[x1, y1, x2, y2] bounding box coordinates in pixels")
    confidence: float = Field(..., ge=0.0, le=1.0)
    class_id: int = Field(0, description="Detected class index")
    label: str = Field("oil", description="Detected class label name")


class ClassificationResponse(BaseModel):
    oil_detected: bool = Field(..., description="True if oil detected by YOLO11n object detector")
    max_confidence: float = Field(..., ge=0.0, le=1.0, description="Maximum detection confidence score")
    oil_probability: float = Field(..., ge=0.0, le=1.0, description="Oil probability score")
    lookalike_probability: float = Field(..., ge=0.0, le=1.0, description="Look-alike probability score")
    classification: str = Field(..., description="'oil' or 'lookalike'")
    detections: List[YOLODetectionBox] = Field(default_factory=list, description="List of detected oil bounding boxes")
    imgsz: int = Field(640, description="YOLO inference image size")
    conf_threshold: float = Field(0.25, description="YOLO confidence threshold")
    model: str = "YOLO11n"
