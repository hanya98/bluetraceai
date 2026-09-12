"""
run_model1_to_model3.py
========================
Glue script: Model 1 checkpoint inference -> SpillRecord -> Model 3 pipeline.

IMPORTANT LIMITATION (be upfront about this in your submission):
------------------------------------------------------------------
The "Refined Deep-SAR Oil Spill (SOS)" dataset used to train Model 1 ships
as plain 256x256 PNG crops with NO geospatial metadata (no GeoTIFF bounds,
no STAC item, no lat/lon corners). Model 1's output is therefore a mask in
PIXEL space only -- it cannot, by itself, produce a real-world centroid.

To bridge Model 1 -> Model 3 today, this script converts the mask centroid
to lat/lon using a SCENE_BOUNDS box you supply by hand below (the
geographic footprint of whatever Sentinel-1 scene the 256x256 crop came
from). This is a stand-in for what a real deployment needs: the backend/
ingestion pipeline should attach each SAR crop's true footprint (from the
Sentinel-1 product metadata) BEFORE calling Model 1, so this conversion can
be exact instead of manual. Flag this as a known gap, not a solved problem.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from model3 import SpillRecord, EnvironmentalRecord
from model3.pipeline import Model3Pipeline
from model3.config import Model3Config

# ---------------------------------------------------------------------
# 1. Import your Model 1 architecture.
#    Easiest: save the AttentionUNet class (+ ConvBlock/DownBlock/
#    AttentionGate/UpBlock) into a file model1_arch.py next to this
#    script, then uncomment the import below.
# ---------------------------------------------------------------------
# from model1_arch import AttentionUNet

CHECKPOINT_PATH = "attention_unet_best.pth"   # your saved checkpoint
IMAGE_PATH = "sample_scene.png"               # the SAR crop to run inference on
THRESHOLD = 0.5                                # or your best_threshold from the sweep

# --- MANUAL GEOREFERENCE (see limitation note above) -------------------
# (min_lat, min_lon, max_lat, max_lon) for the scene this crop came from.
# Replace with the real footprint if/when you have it.
SCENE_BOUNDS = (18.90, 72.70, 19.20, 73.00)


def load_model1(checkpoint_path: str, device: torch.device):
    from model1_arch import AttentionUNet  # local import so the script fails loudly if missing
    model = AttentionUNet(in_channels=1, out_channels=1, base_channels=32).to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()
    return model


def run_inference(model, image_path: str, device: torch.device, threshold: float = 0.5):
    img = Image.open(image_path).convert("L")
    arr = np.array(img, dtype=np.float32) / 255.0
    x = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).to(device)  # (1,1,H,W)

    with torch.no_grad():
        logits = model(x)
        probs = torch.sigmoid(logits)
        mask = (probs > threshold).float().cpu().squeeze().numpy()  # (H,W) in {0,1}

    return mask


def mask_pixel_centroid(mask: np.ndarray):
    """Returns (row, col) centroid of the positive-class pixels, or None if empty."""
    ys, xs = np.where(mask > 0)
    if len(ys) == 0:
        return None
    return float(ys.mean()), float(xs.mean())


def pixel_to_latlon(row, col, mask_shape, bounds):
    """Bilinear map of pixel (row, col) -> (lat, lon) given scene bounds.
    row=0 is the TOP of the image -> max_lat. Adjust if your data is flipped."""
    h, w = mask_shape
    min_lat, min_lon, max_lat, max_lon = bounds
    lat = max_lat - (row / h) * (max_lat - min_lat)
    lon = min_lon + (col / w) * (max_lon - min_lon)
    return lat, lon


def mask_area_km2(mask: np.ndarray, bounds):
    """Very rough area estimate from pixel count * approx km/pixel. Good enough
    for a priority signal, NOT for anything requiring survey-grade accuracy."""
    min_lat, min_lon, max_lat, max_lon = bounds
    h, w = mask.shape
    km_per_deg_lat = 111.0
    km_per_deg_lon = 111.0 * np.cos(np.radians((min_lat + max_lat) / 2))
    px_h_km = (max_lat - min_lat) * km_per_deg_lat / h
    px_w_km = (max_lon - min_lon) * km_per_deg_lon / w
    px_area_km2 = px_h_km * px_w_km
    return float(mask.sum() * px_area_km2)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not Path(CHECKPOINT_PATH).exists():
        raise FileNotFoundError(
            f"{CHECKPOINT_PATH} not found -- copy your .pth from Colab/Drive next to this script."
        )
    if not Path(IMAGE_PATH).exists():
        raise FileNotFoundError(
            f"{IMAGE_PATH} not found -- point this at a real SAR crop you want to run end-to-end."
        )

    model = load_model1(CHECKPOINT_PATH, device)
    mask = run_inference(model, IMAGE_PATH, device, THRESHOLD)

    centroid_px = mask_pixel_centroid(mask)
    if centroid_px is None:
        print("Model 1 found no oil pixels above threshold -- nothing to hand to Model 3.")
        return

    lat, lon = pixel_to_latlon(*centroid_px, mask.shape, SCENE_BOUNDS)
    area_km2 = mask_area_km2(mask, SCENE_BOUNDS)
    detection_confidence = float(mask.mean())  # crude proxy; swap for your own confidence metric

    print(f"Pixel centroid: {centroid_px} -> lat/lon: ({lat:.5f}, {lon:.5f})")
    print(f"Estimated area: {area_km2:.2f} km^2")

    spill = SpillRecord(
        spill_id="SPILL_LIVE_001",
        timestamp_utc=datetime.now(timezone.utc),
        centroid=(lat, lon),
        area_km2=area_km2,
        detection_confidence=detection_confidence,
        oil_probability=None,   # fill in once Model 2 (oil vs look-alike) is wired in too
    )

    # --- Replace this with your real AIS pull for the same time/location ---
    raw_ais_records: list[dict] = []
    # e.g. pulled from Global Fishing Watch / AIS provider as plain dicts:
    # {"vessel_id": "...", "timestamp_utc": "...", "latitude": ..., "longitude": ..., ...}

    if not raw_ais_records:
        print("\nNo AIS records supplied -- plug in your real AIS pull for this "
              "spill's time/location to get a ranked candidate list.")
        return

    pipeline = Model3Pipeline(Model3Config())
    result = pipeline.run(spill, raw_ais_records)

    print(result.preprocessing_report.summary())
    print(result.ranked_candidates[["vessel_id", "rank", "candidate_priority_score"]])


if __name__ == "__main__":
    main()