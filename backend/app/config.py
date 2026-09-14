"""
config.py
=========

Centralised settings loaded from environment variables / .env file.
All paths are resolved relative to the project root.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = backend/
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
    # Model Paths
    # ------------------------------------------------------------------ #

    MODEL1_WEIGHTS_PATH: Path = PROJECT_ROOT / "weights" / "attention_unet_best.pth"

    MODEL1_IN_CHANNELS: int = 1
    MODEL1_OUT_CHANNELS: int = 1
    MODEL1_BASE_CHANNELS: int = 32
    MODEL1_INPUT_SIZE: int = 256
    MODEL1_THRESHOLD: float = 0.5

    MODEL2_WEIGHTS_PATH: Path = PROJECT_ROOT / "weights" / "best.pt"
    MODEL2_IMGSZ: int = 640
    MODEL2_CONF: float = 0.25

    MODEL3_PACKAGE_DIR: Path = (
        PROJECT_ROOT / "MODEL3_SIH_2026-main" / "MODEL3_SIH_2026-main"
    )
    MODEL3_MODE: str = "heuristic"

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #

    DATABASE_URL: str = (
        "postgresql+asyncpg://bluetrace:bluetrace@localhost:5432/bluetrace"
    )

    # ------------------------------------------------------------------ #
    # External APIs
    # ------------------------------------------------------------------ #

    # Copernicus
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

    # Open-Meteo
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"

    # ------------------------------------------------------------------ #
    # HTTP Client
    # ------------------------------------------------------------------ #

    HTTP_TIMEOUT: float = 30.0
    HTTP_MAX_CONNECTIONS: int = 20

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #

    # Optional environment variable for deployed frontend
    FRONTEND_URL: Optional[str] = None

    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            # Local Development
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:5173",
            "http://127.0.0.1:5173",

            # Production Frontend
            "https://bluetraceai.vercel.app",
            "https://bluetrace-ai.vercel.app",

            # Add your deployed frontend here if it's on Render
            # "https://your-frontend.onrender.com",
        ]
    )

    # ------------------------------------------------------------------ #
    # Inference
    # ------------------------------------------------------------------ #

    INFERENCE_DEVICE: str = "cpu"

    AIS_LOOKBACK_HOURS: int = 12
    SPILL_SEARCH_RADIUS_KM: float = 50.0

    # ------------------------------------------------------------------ #
    # Post Init
    # ------------------------------------------------------------------ #

    def model_post_init(self, __context) -> None:
        """Append deployed frontend URL from environment if provided."""
        if self.FRONTEND_URL and self.FRONTEND_URL not in self.ALLOWED_ORIGINS:
            self.ALLOWED_ORIGINS.append(self.FRONTEND_URL)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings object."""
    return Settings()