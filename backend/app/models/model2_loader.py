"""
models/model2_loader.py
======================

Model 2 loader — Ultralytics YOLO11n oil spill look-alike object detection.

Loads trained checkpoint `weights/best.pt` for inference.

Inference parameters match oil-spill-lookalike-classifier (1).ipynb:
 - imgsz = 640
 - conf = 0.25
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any, Dict, Union

from PIL import Image
from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Ultralytics Import
# ---------------------------------------------------------------------

try:
    from ultralytics import YOLO

    ULTRALYTICS_AVAILABLE = True

except Exception as e:
    ULTRALYTICS_AVAILABLE = False
    YOLO = None
    logger.exception("Failed to import Ultralytics: %s", e)


# ---------------------------------------------------------------------
# Model Wrapper
# ---------------------------------------------------------------------


class Model2Inference:
    """Wrapper for Ultralytics YOLO11n oil spill detector."""

    def __init__(self, weights_path: Path, device: str = "cpu") -> None:
        self.settings = get_settings()
        self.weights_path = Path(weights_path)
        self.device = device
        self.model = None

        if not ULTRALYTICS_AVAILABLE:
            logger.warning(
                "Ultralytics import failed. Model 2 will operate in stub mode."
            )
            return

        if not self.weights_path.exists():
            logger.warning(
                f"Model 2 weight file not found at {self.weights_path}. "
                "Operating in stub mode."
            )

    # -----------------------------------------------------------------
    # Lazy Loader
    # -----------------------------------------------------------------

    def _load_model(self):
        """Load YOLO model only when first inference request arrives."""

        if self.model is not None:
            return self.model

        if not ULTRALYTICS_AVAILABLE:
            return None

        if not self.weights_path.exists():
            return None

        try:
            logger.info(
                f"Loading Model 2 (YOLO11n) from {self.weights_path}..."
            )
            self.model = YOLO(str(self.weights_path))
            logger.info("Model 2 loaded successfully.")
            return self.model

        except Exception as e:
            logger.exception("Failed to load YOLO checkpoint: %s", e)
            self.model = None
            return None

    # -----------------------------------------------------------------
    # Prediction
    # -----------------------------------------------------------------

    def predict(self, image_input: Union[bytes, Image.Image]) -> Dict[str, Any]:
        """
        Run YOLO11n object detection on image crop from Model 1.
        """

        if isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")

        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")

        else:
            raise ValueError(f"Unsupported image_input type: {type(image_input)}")

        model = self._load_model()

        # -------------------------------------------------------------
        # Stub fallback
        # -------------------------------------------------------------
        if model is None:
            logger.warning("Running Model 2 in stub fallback mode.")

            return {
                "oil_detected": True,
                "max_confidence": 0.88,
                "oil_probability": 0.88,
                "lookalike_probability": 0.12,
                "classification": "oil",
                "detections": [
                    {
                        "box": [0.0, 0.0, float(img.width), float(img.height)],
                        "confidence": 0.88,
                        "class_id": 0,
                        "label": "oil",
                    }
                ],
                "imgsz": self.settings.MODEL2_IMGSZ,
                "conf_threshold": self.settings.MODEL2_CONF,
                "model": "YOLO11n",
                "status": "stub_fallback",
            }

        # -------------------------------------------------------------
        # Real YOLO Inference
        # -------------------------------------------------------------
        results = model.predict(
            source=img,
            imgsz=self.settings.MODEL2_IMGSZ,
            conf=self.settings.MODEL2_CONF,
            device=self.device,
            verbose=False,
        )

        detections = []
        max_conf = 0.0
        oil_detected = False

        if results:
            res = results[0]
            boxes = res.boxes

            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    xyxy = box.xyxy[0].tolist()
                    conf = float(box.conf[0].item())
                    cls_id = int(box.cls[0].item())

                    label = (
                        res.names.get(cls_id, "oil")
                        if hasattr(res, "names")
                        else "oil"
                    )

                    max_conf = max(max_conf, conf)

                    detections.append(
                        {
                            "box": [round(c, 2) for c in xyxy],
                            "confidence": round(conf, 4),
                            "class_id": cls_id,
                            "label": label,
                        }
                    )

                oil_detected = len(detections) > 0

        max_conf = round(max_conf, 4)
        oil_probability = max_conf if oil_detected else 0.0
        lookalike_probability = round(1.0 - oil_probability, 4)

        return {
            "oil_detected": oil_detected,
            "max_confidence": max_conf,
            "oil_probability": oil_probability,
            "lookalike_probability": lookalike_probability,
            "classification": "oil" if oil_detected else "lookalike",
            "detections": detections,
            "imgsz": self.settings.MODEL2_IMGSZ,
            "conf_threshold": self.settings.MODEL2_CONF,
            "model": "YOLO11n",
            "status": "success",
        }