"""
services/attribution.py
========================
Model 3 Vessel Attribution service:
  - Invokes Model 3 pipeline to rank candidate vessels
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.models.model3_loader import Model3Inference

logger = logging.getLogger(__name__)


class AttributionService:
    """Service for running Model 3 candidate vessel attribution."""

    def __init__(self, model3: Model3Inference) -> None:
        self.model3 = model3

    async def attribute_vessels(
        self,
        spill_data: Dict[str, Any],
        raw_ais_records: List[Dict[str, Any]],
        environmental_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run vessel attribution pipeline in thread executor.
        """
        loop = asyncio.get_running_loop()

        result = await loop.run_in_executor(
            None,
            lambda: self.model3.run_attribution(
                spill_data=spill_data,
                raw_ais_records=raw_ais_records,
                environmental_data=environmental_data,
            ),
        )

        return result
