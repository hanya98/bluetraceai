"""
services/classification.py
==========================
Model 2 Look-alike Verification service:
  - Invokes Model 2 CNN in a thread executor
  - Returns oil vs look-alike probabilities
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Union
from PIL import Image

from app.models.model2_loader import Model2Inference

logger = logging.getLogger(__name__)


class ClassificationService:
    """Service for running Model 2 oil vs look-alike CNN verification."""

    def __init__(self, model2: Model2Inference) -> None:
        self.model2 = model2

    async def classify_spill(
        self,
        image_bytes: bytes,
    ) -> Dict[str, Any]:
        """
        Run oil vs look-alike CNN classification in executor thread.
        """
        loop = asyncio.get_running_loop()

        result = await loop.run_in_executor(
            None,
            lambda: self.model2.predict(image_bytes),
        )

        return result
