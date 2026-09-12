# BlueTrace Backend — System Flow Architecture

> **SIH 2026 Problem Statement PS-26143: AI-Based Oil Spill Detection and Vessel Attribution**

---

## 1. End-to-End Orchestration Flow Diagram

```
[ Next.js Frontend / Client ]
             │
             │  POST /api/v1/analyze (SAR Image File + Lat/Lon)
             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Orchestrator                            │
└────────────────────────────────────────────────────────────────────────┘
             │
             │  (1) Raw SAR Image Bytes
             ▼
┌────────────────────────────────────────────────────────────────────────┐
│   Model 1: Attention U-Net Segmentation                                │
│   - Resizes tile to 256x256, normalizes intensity                      │
│   - Generates binary segmentation mask                                 │
│   - Calculates confidence & pixel bounds                               │
└────────────────────────────────────────────────────────────────────────┘
             │
             ├────────────────────────┐
             │                        │ (Candidate Spill Pixel Bounds)
             ▼                        ▼
┌─────────────────────────┐  ┌──────────────────────────────────────────┐
│   Geospatial Engine     │  │   Spill Candidate Region Cropping        │
│   (Rasterio & Shapely)  │  │   - Crops bounding box with padding      │
│   - Affine Transform    │  └──────────────────────────────────────────┘
│   - GeoJSON Polygon     │                   │
│   - Area (km²) & Centroid                   │ (Cropped Image Region)
└─────────────────────────┘                   ▼
             │               ┌──────────────────────────────────────────┐
             │               │   Model 2: Ultralytics YOLO11n Detector  │
             │               │   - Inference: imgsz=640, conf=0.25      │
             │               │   - Returns bounding boxes & confidence  │
             │               │   - Verifies Oil vs Look-alike           │
             │               └──────────────────────────────────────────┘
             │                                │
             └────────────────────────────────┤ (GeoJSON + Oil Conf)
                                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        External Data Ingestion                         │
│                                                                        │
│   ├── Open-Meteo Weather API (Wind Speed & Ocean Direction)           │
│   └── Global Fishing Watch / Cached AIS (Candidate Vessel Tracks)     │
└────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│   Model 3: AIS Vessel Attribution Engine                               │
│   - Drift model integration & spatiotemporal trajectory alignment       │
│   - XGBoost / Heuristic candidate ranking                              │
│   - Guarded non-causal explainability output                            │
└────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Unified RFC 7946 GeoJSON Response                    │
└────────────────────────────────────────────────────────────────────────┘
             │
             │  JSON Payload
             ▼
[ Next.js MapLibre Interactive Dashboard ]
```

---

## 2. Step-by-Step Pipeline Mechanics

### Step 1: Request Ingestion (`POST /api/v1/analyze`)
The client posts a Synthetic Aperture Radar (SAR) scene image tile alongside spatial center coordinates (`lat`, `lon`).

### Step 2: Segmentation & Vectorization (Model 1)
- The raw image is passed to `Model1Inference` (`AttentionUNet`).
- Preprocessing converts the image to grayscale, normalizes intensities by `255.0`, and resizes to `256×256`.
- A probability heatmap is generated, thresholded at `0.5` to yield a binary mask.
- `geo_utils.py` applies Rasterio `Affine` transforms to convert mask pixels into WGS84 GeoJSON polygons (`Polygon` / `MultiPolygon`), computing centroid coordinates and equal-area projection spill area in km².

### Step 3: Oil vs. Look-Alike Verification (Model 2)
- The pixel bounding box of the detected spill is cropped from the original SAR image with contextual margin padding.
- The cropped image region is passed to `Model2Inference` (`Ultralytics YOLO11n`).
- YOLO11n runs inference at `imgsz=640` and `conf=0.25` to detect oil slicks and discriminate them from natural look-alikes (e.g. low-wind areas, biogenic films).

### Step 4: Environmental & Vessel Track Retrieval
- **Weather Service**: Asynchronously fetches surface wind speed (m/s) and wind direction from Open-Meteo API.
- **AIS Service**: Queries vessel positions within a 50 km radius during a 12-hour lookback window from Global Fishing Watch (or local cached AIS dataset).

### Step 5: Vessel Attribution (Model 3)
- `SpillRecord`, `AISObservation`, and `EnvironmentalRecord` data structures are constructed.
- `Model3Pipeline` projects oil drift backwards along wind/current vectors to score and rank candidate vessels.
- Outputs non-causal explanations avoiding guilt-implying terms.

### Step 6: Unified Response Delivery
The backend aggregates detection polygons, YOLO bounding boxes, weather records, and ranked candidate vessels into a single JSON payload rendered by MapLibre on the frontend.
