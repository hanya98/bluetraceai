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
from typing import Any, Dict, List, Union
from PIL import Image

from app.config import get_settings

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    YOLO = None


class Model2Inference:
    """Wrapper for Ultralytics YOLO11n oil spill detector."""

    def __init__(self, weights_path: Path, device: str = "cpu") -> None:
        self.settings = get_settings()
        self.weights_path = Path(weights_path)
        self.device = device
        self.model = None

        if not ULTRALYTICS_AVAILABLE:
            logger.warning("ultralytics package is not installed. Model 2 inference will operate in stub mode.")
            return

        if self.weights_path.exists():
            try:
                self.model = YOLO(str(self.weights_path))
                logger.info(f"Model 2 (YOLO11n) loaded successfully from {self.weights_path}")
            except Exception as e:
                logger.error(f"Failed to load Model 2 YOLO weights from {self.weights_path}: {e}")
                self.model = None
        else:
            logger.warning(
                f"Model 2 weight file not found at {self.weights_path}. "
                "Place trained `best.pt` in `weights/` directory for live YOLO inference. Operating in stub mode."
            )

    def predict(self, image_input: Union[bytes, Image.Image]) -> Dict[str, Any]:
        """
        Run YOLO11n object detection on image crop from Model 1.

        Returns:
          - oil_detected: bool
          - max_confidence: float
          - detections: List[Dict[str, Any]] (bounding boxes, confidence, class label)
          - classification: "oil" or "lookalike"
          - oil_probability: float
          - lookalike_probability: float
        """
        if isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        else:
            raise ValueError(f"Unsupported image_input type: {type(image_input)}")

        if self.model is None:
            # Fallback when weights file not present in local environment
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

        # Run inference using Ultralytics YOLO with notebook hyperparams imgsz=640, conf=0.25
        results = self.model.predict(
            source=img,
            imgsz=self.settings.MODEL2_IMGSZ,
            conf=self.settings.MODEL2_CONF,
            device=self.device,
            verbose=False,
        )

        detections = []
        max_conf = 0.0
        oil_detected = False

        if results and len(results) > 0:
            res = results[0]
            boxes = res.boxes
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    conf = float(box.conf[0].item())
                    cls_id = int(box.cls[0].item())
                    label = res.names.get(cls_id, "oil") if hasattr(res, "names") else "oil"

                    if conf > max_conf:
                        max_conf = conf

                    detections.append({
                        "box": [round(c, 2) for c in xyxy],
                        "confidence": round(conf, 4),
                        "class_id": cls_id,
                        "label": label,
                    })

                oil_detected = len(detections) > 0

        max_conf_rounded = round(max_conf, 4)
        oil_prob = max_conf_rounded if oil_detected else 0.0
        lookalike_prob = round(1.0 - oil_prob, 4)

        return {
            "oil_detected": oil_detected,
            "max_confidence": max_conf_rounded,
            "oil_probability": oil_prob,
            "lookalike_probability": lookalike_prob,
            "classification": "oil" if oil_detected else "lookalike",
            "detections": detections,
            "imgsz": self.settings.MODEL2_IMGSZ,
            "conf_threshold": self.settings.MODEL2_CONF,
            "model": "YOLO11n",
            "status": "success",
        }
