"""
services/spill_detection.py
===========================
Model 1 Spill Detection service:
  - Invokes Model1Inference safely in an executor thread
  - Converts pixel binary mask -> GeoJSON polygon using Rasterio Affine transforms
  - Calculates centroid, area (km²), bounding box, and crops candidate spill region for Model 2
"""
from __future__ import annotations

import io
import asyncio
import logging
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
from PIL import Image

from app.models.model1_loader import Model1Inference
from app.utils.geo_utils import calculate_centroid_and_area, mask_to_geojson_polygon

logger = logging.getLogger(__name__)


class SpillDetectionService:
    """Service for running Model 1 inference, geospatial post-processing, and region cropping."""

    def __init__(self, model1: Model1Inference) -> None:
        self.model1 = model1

    async def detect_spill(
        self,
        image_bytes: bytes,
        center_lat: float = 19.05,
        center_lon: float = 72.85,
        threshold: Optional[float] = None,
        pixel_scale_km: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Run AttentionUNet inference on image, compute geospatial metadata,
        and generate cropped spill candidate region for Model 2 classification.
        """
        loop = asyncio.get_running_loop()

        # Run CPU inference in thread pool
        pred_result = await loop.run_in_executor(
            None,
            lambda: self.model1.predict(image_bytes, threshold=threshold),
        )

        binary_mask = pred_result["binary_mask"]
        spill_detected = pred_result["spill_detected"]
        confidence = pred_result["confidence"]

        if not spill_detected:
            return {
                "spill_detected": False,
                "confidence": round(confidence, 4),
                "centroid": None,
                "area_km2": 0.0,
                "bounding_box": None,
                "mask_polygon": None,
                "pixel_mask_shape": list(binary_mask.shape),
                "crop_bytes": None,
                "model": "AttentionUNet",
                "threshold_used": threshold or 0.5,
            }

        # Vectorize mask -> GeoJSON polygon
        polygon = mask_to_geojson_polygon(
            binary_mask,
            center_lat=center_lat,
            center_lon=center_lon,
            pixel_scale_km=pixel_scale_km,
        )

        centroid, area_km2, bbox = calculate_centroid_and_area(
            binary_mask,
            center_lat=center_lat,
            center_lon=center_lon,
            pixel_scale_km=pixel_scale_km,
        )

        # Crop candidate spill region for Model 2 CNN
        crop_bytes = self._crop_spill_region(image_bytes, binary_mask)

        return {
            "spill_detected": True,
            "confidence": round(confidence, 4),
            "centroid": {"lat": centroid[0], "lon": centroid[1]} if centroid else None,
            "area_km2": area_km2,
            "bounding_box": bbox,
            "mask_polygon": polygon,
            "pixel_mask_shape": list(binary_mask.shape),
            "crop_bytes": crop_bytes,
            "model": "AttentionUNet",
            "threshold_used": threshold or 0.5,
        }

    def _crop_spill_region(self, image_bytes: bytes, binary_mask: np.ndarray, padding_px: int = 15) -> bytes:
        """
        Crops the bounding box region of detected oil spill candidate from the source image.
        Adds padding_px for spatial context.
        """
        img = Image.open(io.BytesIO(image_bytes))
        orig_w, orig_h = img.size

        y_indices, x_indices = np.where(binary_mask > 0)
        if len(x_indices) == 0:
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()

        mask_h, mask_w = binary_mask.shape
        scale_x = float(orig_w) / float(mask_w)
        scale_y = float(orig_h) / float(mask_h)

        min_x = max(0, int(np.min(x_indices) * scale_x) - padding_px)
        max_x = min(orig_w, int(np.max(x_indices) * scale_x) + padding_px)
        min_y = max(0, int(np.min(y_indices) * scale_y) - padding_px)
        max_y = min(orig_h, int(np.max(y_indices) * scale_y) + padding_px)

        cropped_img = img.crop((min_x, min_y, max_x, max_y))
        buffer = io.BytesIO()
        cropped_img.save(buffer, format="PNG")
        return buffer.getvalue()
