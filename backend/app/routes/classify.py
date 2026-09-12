"""
routes/classify.py
==================
POST /api/v1/classify (Internal / Debug Endpoint)
Endpoint for Model 2 oil vs look-alike CNN verification.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.dependencies import get_model2
from app.models.model2_loader import Model2Inference
from app.schemas.classification import ClassificationResponse
from app.services.classification import ClassificationService

router = APIRouter(tags=["Internal / Debug"])


@router.post("/classify", response_model=ClassificationResponse, summary="[Internal/Debug] Model 2 Classification Test")
async def classify_spill_crop(
    file: UploadFile = File(..., description="SAR crop image file"),
    model2: Model2Inference = Depends(get_model2),
):
    """
    [Internal/Debug] Run Model 2 (Oil vs Look-alike CNN) on SAR spill crop.
    Returns probabilities for oil vs look-alike.
    """
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded crop image is empty.")

    service = ClassificationService(model2)
    result = await service.classify_spill(image_bytes)
    return result
