"""
routes/detect.py
================
POST /api/v1/detect-spill (Internal / Debug Endpoint)
Endpoint for running Model 1 AttentionUNet segmentation on uploaded SAR images.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.dependencies import get_model1
from app.models.model1_loader import Model1Inference
from app.schemas.detection import DetectionResponse
from app.services.spill_detection import SpillDetectionService

router = APIRouter(tags=["Internal / Debug"])


@router.post("/detect-spill", response_model=DetectionResponse, summary="[Internal/Debug] Model 1 Segmentation Test")
async def detect_spill(
    file: UploadFile = File(..., description="SAR image file (PNG, JPG, or GeoTIFF)"),
    lat: float = Form(19.05, ge=-90.0, le=90.0, description="Center latitude of image"),
    lon: float = Form(72.85, ge=-180.0, le=180.0, description="Center longitude of image"),
    threshold: Optional[float] = Form(0.5, ge=0.0, le=1.0, description="Binary threshold"),
    pixel_scale_km: float = Form(0.01, description="KM per pixel"),
    model1: Model1Inference = Depends(get_model1),
):
    """
    [Internal/Debug] Run Model 1 (Attention UNet) on SAR image tile.
    Returns binary mask polygon (GeoJSON), centroid, area (km2), and confidence.
    """
    if not file.content_type.startswith("image/") and not file.filename.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Upload a PNG, JPG, or TIFF SAR image file.",
        )

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    service = SpillDetectionService(model1)
    result = await service.detect_spill(
        image_bytes=image_bytes,
        center_lat=lat,
        center_lon=lon,
        threshold=threshold,
        pixel_scale_km=pixel_scale_km,
    )
    result.pop("crop_bytes", None)

    return result
