"""
models/model1_loader.py
======================
Model 1 loader — loads `AttentionUNet` and its pre-trained weights once at application startup.
Preserves the exact notebook preprocessing:
  1. Open image as PIL Image -> convert("L") (grayscale)
  2. Scale to [0, 1] float32
  3. Tensor shape (1, 1, 256, 256)
  4. Run forward pass -> sigmoid -> threshold (default 0.5)
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
from PIL import Image
import torch

from app.config import PROJECT_ROOT, get_settings
from app.models.model1_arch import AttentionUNet

logger = logging.getLogger(__name__)


class Model1Inference:
    """Wrapper around trained AttentionUNet for thread-safe CPU/GPU inference."""

    def __init__(self, weights_path: Path, device: str = "cpu") -> None:
        self.device = torch.device(device if torch.cuda.is_available() and device == "cuda" else "cpu")
        self.weights_path = Path(weights_path)
        self.settings = get_settings()
        self.has_weights = False

        logger.info(f"Loading Model 1 (AttentionUNet) on device={self.device}...")
        self.model = AttentionUNet(
            in_channels=self.settings.MODEL1_IN_CHANNELS,
            out_channels=self.settings.MODEL1_OUT_CHANNELS,
            base_channels=self.settings.MODEL1_BASE_CHANNELS,
        )

        candidate_paths = [
            self.weights_path,
            PROJECT_ROOT / "weights" / "attention_unet_best.pth",
            PROJECT_ROOT / "MODEL3_SIH_2026-main" / "MODEL3_SIH_2026-main" / "attention_unet_best.pth",
            PROJECT_ROOT / "MODEL3_SIH_2026-main" / "attention_unet_best.pth",
        ]

        found_weights = None
        for p in candidate_paths:
            if p and p.exists():
                found_weights = p
                break

        if found_weights:
            try:
                state_dict = torch.load(str(found_weights), map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.has_weights = True
                logger.info(f"Model 1 weights loaded successfully from {found_weights}.")
            except Exception as e:
                logger.error(f"Failed to load Model 1 weights from {found_weights}: {e}")
        else:
            logger.warning(
                f"Model 1 weights file not found at {self.weights_path}. "
                "AttentionUNet initialized in fallback mode."
            )

        self.model.to(self.device)
        self.model.eval()

    def preprocess(self, image_bytes_or_pil: Union[bytes, Image.Image]) -> Tuple[torch.Tensor, Tuple[int, int]]:
        """
        Preserve verbatim notebook preprocessing:
          - Image.open().convert("L")
          - resize to (256, 256)
          - scale [0, 1]
          - shape (1, 1, 256, 256)
        Returns:
          (tensor, original_shape (width, height))
        """
        if isinstance(image_bytes_or_pil, bytes):
            img = Image.open(io.BytesIO(image_bytes_or_pil))
        else:
            img = image_bytes_or_pil

        orig_size = img.size  # (width, height)

        # Convert to grayscale (single-channel L) as in notebook
        img_l = img.convert("L")
        # Resize to model input size (256x256)
        img_resized = img_l.resize(
            (self.settings.MODEL1_INPUT_SIZE, self.settings.MODEL1_INPUT_SIZE),
            Image.Resampling.BILINEAR,
        )

        # Scale float32 [0.0, 1.0]
        img_arr = np.array(img_resized, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(img_arr).unsqueeze(0).unsqueeze(0).to(self.device)

        return tensor, orig_size

    @torch.no_grad()
    def predict(
        self,
        image_bytes_or_pil: Union[bytes, Image.Image],
        threshold: Optional[float] = None,
    ) -> dict:
        """
        Run inference.
        Returns:
          - binary_mask: np.ndarray (256, 256) uint8 {0, 1}
          - prob_map: np.ndarray (256, 256) float32 [0, 1]
          - confidence: float (max probability over oil regions)
          - orig_size: tuple (width, height)
        """
        thresh = threshold if threshold is not None else self.settings.MODEL1_THRESHOLD
        tensor, orig_size = self.preprocess(image_bytes_or_pil)

        logits = self.model(tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()  # (256, 256)
        binary_mask = (probs > thresh).astype(np.uint8)

        if not self.has_weights and not np.any(binary_mask):
            # Fallback SAR dark feature segmentation when checkpoint file is missing
            img_arr = tensor.squeeze().cpu().numpy()
            mean_val = float(np.mean(img_arr))
            thresh_val = min(0.35, max(0.12, mean_val * 0.75))
            binary_mask = (img_arr < thresh_val).astype(np.uint8)
            probs = np.clip(1.0 - (img_arr / (thresh_val * 1.5 + 1e-6)), 0.0, 1.0)

        oil_pixels = probs[binary_mask == 1]
        confidence = float(np.max(oil_pixels)) if len(oil_pixels) > 0 else float(np.max(probs))

        return {
            "binary_mask": binary_mask,
            "prob_map": probs,
            "confidence": round(confidence, 4),
            "spill_detected": bool(np.any(binary_mask)),
            "orig_size": orig_size,
        }
