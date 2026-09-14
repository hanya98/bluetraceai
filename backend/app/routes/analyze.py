"""
routes/analyze.py
=================
POST /api/v1/analyze — Primary Orchestrating Public Endpoint.

Pipeline Flow:
  1. Receive SAR image + location metadata
  2. Model 1 (AttentionUNet): Run segmentation -> produce binary mask, GeoJSON polygon, & cropped spill candidate region
  3. Model 2 (CNN): Run look-alike verification on CROPPED spill region (not full image) -> oil probability
  4. External Weather API: Fetch ocean wind speed & direction
  5. External AIS API: Fetch candidate vessel trajectories near spill centroid
  6. Model 3 (Model3Pipeline): Run vessel attribution -> rank candidate vessels
  7. Return unified response payload for Next.js frontend map.
"""
from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.dependencies import get_model1, get_model2, get_model3
from app.external.ais_client import AISClient
from app.external.weather_client import WeatherClient
from app.models.model1_loader import Model1Inference
from app.models.model2_loader import Model2Inference
from app.models.model3_loader import Model3Inference
from app.schemas.pipeline import FullAnalysisResponse
from app.services.attribution import AttributionService
from app.services.classification import ClassificationService
from app.services.spill_detection import SpillDetectionService

router = APIRouter(tags=["ML Pipeline Orchestration (Public)"])


@router.post("/analyze", response_model=FullAnalysisResponse, summary="Primary Public ML Pipeline Endpoint")
async def run_full_analysis(
    file: UploadFile = File(..., description="SAR scene image file (PNG, JPG, TIFF)"),
    lat: float = Form(19.05, ge=-90.0, le=90.0, description="Scene center latitude"),
    lon: float = Form(72.85, ge=-180.0, le=180.0, description="Scene center longitude"),
    spill_id: Optional[str] = Form(None, description="Optional custom spill ID"),
    search_radius_km: float = Form(50.0, ge=5.0, le=200.0),
    model1: Model1Inference = Depends(get_model1),
    model2: Model2Inference = Depends(get_model2),
    model3: Model3Inference = Depends(get_model3),
):
    """
    Primary Public Orchestration Endpoint (POST /api/v1/analyze).

    Executes full pipeline:
      1. Model 1 (Segmentation) -> GeoJSON polygon + cropped spill candidate region
      2. Model 2 (Classification) -> verification of cropped region (oil vs look-alike)
      3. Weather API -> ocean wind parameters
      4. AIS API -> candidate vessel tracks
      5. Model 3 (Attribution) -> vessel ranking & non-causal explanation.
    """
    analysis_id = spill_id or f"SPILL_{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image file uploaded.")

    # ------------------------------------------------------------------ #
    # Step 1: Model 1 Segmentation & Geospatial Polygon Extraction
    # ------------------------------------------------------------------ #
    detection_svc = SpillDetectionService(model1)
    detection_res = await detection_svc.detect_spill(
        image_bytes=image_bytes,
        center_lat=lat,
        center_lon=lon,
    )

    crop_bytes = detection_res.pop("crop_bytes", None)

    if not detection_res["spill_detected"]:
        return FullAnalysisResponse(
            analysis_id=analysis_id,
            timestamp_utc=now,
            location={"lat": lat, "lon": lon},
            detection=detection_res,
            classification=None,
            weather=None,
            attribution=None,
            summary="No oil spill detected in the provided SAR image.",
        )

    # ------------------------------------------------------------------ #
    # Step 2: Model 2 Verification on CROPPED Spill Region
    # ------------------------------------------------------------------ #
    input_for_model2 = crop_bytes if crop_bytes else image_bytes
    classification_svc = ClassificationService(model2)
    classification_res = await classification_svc.classify_spill(input_for_model2)

    # ------------------------------------------------------------------ #
    # Step 3: Weather Data Retrieval (Open-Meteo)
    # ------------------------------------------------------------------ #
    centroid_lat = detection_res["centroid"]["lat"] if detection_res["centroid"] else lat
    centroid_lon = detection_res["centroid"]["lon"] if detection_res["centroid"] else lon

    weather_client = WeatherClient()
    weather_data = await weather_client.get_wind_data(lat=centroid_lat, lon=centroid_lon)

    # ------------------------------------------------------------------ #
    # Step 4: AIS Trajectory Data Retrieval
    # ------------------------------------------------------------------ #
    ais_client = AISClient()
    ais_records = await ais_client.get_nearby_vessels(
        lat=centroid_lat,
        lon=centroid_lon,
        spill_time=now,
        radius_km=search_radius_km,
    )

    # ------------------------------------------------------------------ #
    # Step 5: Model 3 Candidate Vessel Attribution
    # ------------------------------------------------------------------ #
    spill_payload = {
        "spill_id": analysis_id,
        "timestamp_utc": now,
        "centroid": (centroid_lat, centroid_lon),
        "area_km2": detection_res["area_km2"],
        "polygon": detection_res["mask_polygon"]["coordinates"][0] if detection_res["mask_polygon"] else None,
        "oil_probability": classification_res["oil_probability"],
        "detection_confidence": detection_res["confidence"],
    }

    attribution_svc = AttributionService(model3)
    attribution_res = await attribution_svc.attribute_vessels(
        spill_data=spill_payload,
        raw_ais_records=ais_records,
        environmental_data=weather_data,
    )

    # Summary phrasing
    top_vessels = attribution_res.get("ranked_vessels", [])

    if top_vessels:
        top_vessel_id = top_vessels[0].get("vessel_id", "N/A")
        summary = (
        f"Oil spill detected ({detection_res['area_km2']} km²) with "
        f"{classification_res['oil_probability']*100:.1f}% oil confidence. "
        f"Candidate vessel {top_vessel_id} ranked highest priority for verification."
        )
    else:
        summary = (
        f"Oil spill detected ({detection_res['area_km2']} km²) with "
        f"{classification_res['oil_probability']*100:.1f}% oil confidence. "
        "No candidate vessels found within the search radius."
        )

    return FullAnalysisResponse(
        analysis_id=analysis_id,
        timestamp_utc=now,
        location={"lat": centroid_lat, "lon": centroid_lon},
        detection=detection_res,
        classification=classification_res,
        weather=weather_data,
        attribution=attribution_res,
        summary=summary,
    )
