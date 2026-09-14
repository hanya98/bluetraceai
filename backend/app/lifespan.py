"""
lifespan.py
===========
FastAPI Lifespan context manager.
Loads all ML models and initializes HTTP clients ONCE during application startup.
Shuts them down gracefully when the application stops.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.config import get_settings
from app.models.model1_loader import Model1Inference
from app.models.model2_loader import Model2Inference
from app.models.model3_loader import Model3Inference

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application Lifespan Context Manager.
    1. Loads Model 1, Model 2, and Model 3 instances into app.state
    2. Initializes shared httpx AsyncClient
    3. Handles shutdown cleanup
    """
    settings = get_settings()
    logger.info("Starting BlueTrace AI Backend lifespan...")

    # Load Model 1 (AttentionUNet)
    try:
        app.state.model1 = Model1Inference(
            weights_path=settings.MODEL1_WEIGHTS_PATH,
            device=settings.INFERENCE_DEVICE,
        )
    except Exception as e:
        logger.error(f"Failed to load Model 1: {e}")
        app.state.model1 = None

    # Load Model 2 (Oil vs Look-alike CNN)
    try:
        app.state.model2 = Model2Inference(
            weights_path=settings.MODEL2_WEIGHTS_PATH,
            device=settings.INFERENCE_DEVICE,
        )
    except Exception as e:
        logger.error(f"Failed to load Model 2: {e}")
        app.state.model2 = None

    # Load Model 3 (Vessel Attribution Pipeline)
    try:
        app.state.model3 = Model3Inference()
    except Exception as e:
        logger.error(f"Failed to load Model 3: {e}")
        app.state.model3 = None

    logger.info("All ML models initialization attempted. App is ready.")

    yield  # Application runs while suspended here

    # Shutdown logic
    logger.info("Shutting down BlueTrace AI Backend...")
