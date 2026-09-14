"""
dependencies.py
===============
FastAPI Dependency Injection helpers.
Provides singletons for settings, database session, model instances, and external services.
"""
from __future__ import annotations

from typing import AsyncGenerator
from fastapi import Request

from app.config import Settings, get_settings
from app.models.model1_loader import Model1Inference
from app.models.model2_loader import Model2Inference
from app.models.model3_loader import Model3Inference


def get_app_settings() -> Settings:
    """Dependency for Settings."""
    return get_settings()


def get_model1(request: Request) -> Model1Inference:
    """Dependency for Model 1 (AttentionUNet)."""
    model = getattr(request.app.state, "model1", None)
    if model is None:
        raise RuntimeError("Model 1 is not initialized or failed to load.")
    return model


def get_model2(request: Request) -> Model2Inference:
    """Dependency for Model 2 (CNN Classifier)."""
    model = getattr(request.app.state, "model2", None)
    if model is None:
        raise RuntimeError("Model 2 is not initialized or failed to load.")
    return model


def get_model3(request: Request) -> Model3Inference:
    """Dependency for Model 3 (Vessel Attribution)."""
    model = getattr(request.app.state, "model3", None)
    if model is None:
        raise RuntimeError("Model 3 is not initialized or failed to load.")
    return model
