"""
routes/health.py
================
GET /api/v1/health
Health check endpoint reporting detailed ML model status & external API connectivity.
"""
from __future__ import annotations

import httpx
from fastapi import APIRouter, Request

from app.config import get_settings

router = APIRouter(tags=["Health"])


async def check_external_service(url: str, timeout: float = 3.0) -> dict:
    """Helper to check connectivity to external HTTP APIs."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.get(url)
            return {
                "status": "connected" if res.status_code < 500 else "degraded",
                "http_status": res.status_code,
            }
    except Exception as e:
        return {
            "status": "unreachable",
            "error": str(e),
        }


@router.get("/health", summary="Detailed Health & Connectivity Status")
async def health_check(request: Request):
    """
    Returns application health status, ML model loading status,
    and external API connectivity metrics.
    """
    settings = get_settings()

    model1_ok = getattr(request.app.state, "model1", None) is not None
    model2_ok = getattr(request.app.state, "model2", None) is not None
    model3_ok = getattr(request.app.state, "model3", None) is not None

    all_models_ok = model1_ok and model2_ok and model3_ok

    # Check external connectivity
    open_meteo_res = await check_external_service(f"{settings.OPEN_METEO_BASE_URL}/forecast?latitude=19.05&longitude=72.85&current_weather=true")
    copernicus_res = await check_external_service(f"{settings.COPERNICUS_STAC_URL}/search", timeout=3.0)
    gfw_configured = bool(settings.GFW_API_KEY)

    return {
        "status": "healthy" if all_models_ok else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "models": {
            "model1_attention_unet": {
                "status": "loaded" if model1_ok else "failed",
                "weights_path": str(settings.MODEL1_WEIGHTS_PATH),
                "device": settings.INFERENCE_DEVICE,
            },
            "model2_yolo11n_detector": {
                "status": "loaded" if model2_ok else "failed",
                "weights_path": str(settings.MODEL2_WEIGHTS_PATH),
                "imgsz": settings.MODEL2_IMGSZ,
                "conf_threshold": settings.MODEL2_CONF,
            },
            "model3_vessel_attribution": {
                "status": "loaded" if model3_ok else "failed",
                "mode": settings.MODEL3_MODE,
            },
        },
        "external_services": {
            "open_meteo_weather": open_meteo_res,
            "copernicus_stac": copernicus_res,
            "global_fishing_watch_ais": {
                "status": "configured" if gfw_configured else "using_cached_sample_data",
                "api_key_present": gfw_configured,
            },
        },
    }
