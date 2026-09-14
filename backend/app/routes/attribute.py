"""
routes/attribute.py
===================
POST /api/v1/attribution (Internal / Debug Endpoint)
Endpoint for running Model 3 AIS vessel attribution pipeline directly.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_model3
from app.models.model3_loader import Model3Inference
from app.schemas.attribution import AttributionRequest, AttributionResponse
from app.services.attribution import AttributionService

router = APIRouter(tags=["Internal / Debug"])


@router.post("/attribution", response_model=AttributionResponse, summary="[Internal/Debug] Model 3 Attribution Test")
async def attribute_vessels(
    payload: AttributionRequest,
    model3: Model3Inference = Depends(get_model3),
):
    """
    [Internal/Debug] Run Model 3 AIS vessel attribution.
    Ranks candidate vessels near spill centroid using AIS trajectories and environmental data.
    """
    try:
        spill_dict = payload.spill.model_dump()
        spill_dict["centroid"] = payload.spill.centroid.to_tuple()

        ais_list = [ping.model_dump() for ping in payload.ais_records]
        env_dict = payload.environment.model_dump() if payload.environment else None

        service = AttributionService(model3)
        result = await service.attribute_vessels(
            spill_data=spill_dict,
            raw_ais_records=ais_list,
            environmental_data=env_dict,
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model 3 attribution failed: {str(e)}",
        )
