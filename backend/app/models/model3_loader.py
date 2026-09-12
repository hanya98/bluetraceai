"""
models/model3_loader.py
======================
Model 3 loader — Vessel Attribution pipeline wrapper.
Imports and initializes Model3Pipeline from `MODEL3_SIH_2026-main/MODEL3_SIH_2026-main/model3/`.
Injects directory into sys.path dynamically.
"""
from __future__ import annotations

import logging
import sys
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class Model3Inference:
    """Wrapper for Model 3 AIS Vessel Attribution pipeline."""

    def __init__(self) -> None:
        self.settings = get_settings()
        package_dir = str(self.settings.MODEL3_PACKAGE_DIR.resolve())

        if package_dir not in sys.path:
            sys.path.insert(0, package_dir)
            logger.info(f"Added Model 3 directory to sys.path: {package_dir}")

        try:
            from model3.config import Model3Config
            from model3.pipeline import Model3Pipeline
            from model3.schemas import EnvironmentalRecord, SpillRecord

            self.Model3Config = Model3Config
            self.Model3Pipeline = Model3Pipeline
            self.SpillRecord = SpillRecord
            self.EnvironmentalRecord = EnvironmentalRecord

            config = Model3Config(mode=self.settings.MODEL3_MODE)
            self.pipeline = Model3Pipeline(config=config)
            logger.info(f"Model 3 Pipeline initialized successfully in mode='{self.settings.MODEL3_MODE}'.")
        except ImportError as e:
            logger.error(f"Failed to import Model 3 modules from {package_dir}: {e}")
            raise

    def run_attribution(
        self,
        spill_data: Dict[str, Any],
        raw_ais_records: List[Dict[str, Any]],
        environmental_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run vessel attribution pipeline.
        """
        # Convert dictionary to SpillRecord
        spill = self.SpillRecord(
            spill_id=spill_data["spill_id"],
            timestamp_utc=spill_data["timestamp_utc"],
            centroid=spill_data.get("centroid"),
            polygon=spill_data.get("polygon"),
            area_km2=spill_data.get("area_km2"),
            bbox=spill_data.get("bbox"),
            drift_direction_deg=spill_data.get("drift_direction_deg"),
            drift_speed_kmh=spill_data.get("drift_speed_kmh"),
            oil_probability=spill_data.get("oil_probability"),
            detection_confidence=spill_data.get("detection_confidence"),
        )

        env = None
        if environmental_data:
            env = self.EnvironmentalRecord(
                wind_speed_ms=environmental_data.get("wind_speed_ms"),
                wind_direction_deg=environmental_data.get("wind_direction_deg"),
                source=environmental_data.get("source", "open-meteo"),
                is_modelled=environmental_data.get("is_modelled", True),
            )

        result = self.pipeline.run(spill=spill, raw_ais_records=raw_ais_records, environment=env)
        return result.to_api_payload()
