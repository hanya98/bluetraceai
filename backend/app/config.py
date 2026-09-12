"""
config.py
=========
Centralised settings loaded from environment variables / .env file.
All paths are resolved relative to the project root (BlueTrace Backend/).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = the directory that contains the `app/` package
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    APP_NAME: str = "BlueTrace AI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ------------------------------------------------------------------ #
    # Model paths  (relative to PROJECT_ROOT)
    # ------------------------------------------------------------------ #
    # Model 1 — weights produced by untitiled0.ipynb training
    MODEL1_WEIGHTS_PATH: Path = PROJECT_ROOT / "weights" / "attention_unet_best.pth"
    # Model 1 hyperparams (must match notebook exactly)
    MODEL1_IN_CHANNELS: int = 1
    MODEL1_OUT_CHANNELS: int = 1
    MODEL1_BASE_CHANNELS: int = 32
    MODEL1_INPUT_SIZE: int = 256        # resize to 256×256 before inference
    MODEL1_THRESHOLD: float = 0.5

    # Model 2 — Ultralytics YOLO11n weights checkpoint (oil-spill-lookalike-classifier (1).ipynb)
    MODEL2_WEIGHTS_PATH: Path = PROJECT_ROOT / "weights" / "best.pt"
    MODEL2_IMGSZ: int = 640
    MODEL2_CONF: float = 0.25

    # Model 3 — no weight file; package imported directly.
    # sys.path injection handled in lifespan.py.
    MODEL3_PACKAGE_DIR: Path = (
        PROJECT_ROOT / "MODEL3_SIH_2026-main" / "MODEL3_SIH_2026-main"
    )
    MODEL3_MODE: str = "heuristic"      # "heuristic" | "ml"

    # ------------------------------------------------------------------ #
    # Database (PostGIS)
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = "postgresql+asyncpg://bluetrace:bluetrace@localhost:5432/bluetrace"

    # ------------------------------------------------------------------ #
    # External APIs
    # ------------------------------------------------------------------ #
    # Copernicus / Sentinel Hub
    COPERNICUS_CLIENT_ID: Optional[str] = None
    COPERNICUS_CLIENT_SECRET: Optional[str] = None
    COPERNICUS_STAC_URL: str = "https://catalogue.dataspace.copernicus.eu/stac"
    COPERNICUS_TOKEN_URL: str = (
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
        "protocol/openid-connect/token"
    )

    # Global Fishing Watch
    GFW_API_KEY: Optional[str] = None
    GFW_BASE_URL: str = "https://gateway.api.globalfishingwatch.org/v3"

    # Open-Meteo (no API key needed for public endpoint)
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"

    # ------------------------------------------------------------------ #
    # HTTP client
    # ------------------------------------------------------------------ #
    HTTP_TIMEOUT: float = 30.0
    HTTP_MAX_CONNECTIONS: int = 20

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ------------------------------------------------------------------ #
    # Inference
    # ------------------------------------------------------------------ #
    INFERENCE_DEVICE: str = "cpu"       # "cpu" | "cuda"
    AIS_LOOKBACK_HOURS: int = 12        # hours before spill detection to query AIS
    SPILL_SEARCH_RADIUS_KM: float = 50.0  # candidate vessel radius for Model 3


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance."""
    return Settings()
