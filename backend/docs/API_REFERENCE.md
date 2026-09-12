# BlueTrace Backend — Public API Reference

> **SIH 2026 Problem Statement PS-26143: AI-Based Oil Spill Detection and Vessel Attribution**

All API endpoints are mounted under `/api/v1`.

---

## 1. POST `/api/v1/analyze`

**Purpose**: Primary public ML pipeline orchestrator endpoint. Accepts a SAR scene image file and location metadata, executes segmentation (Model 1), crops candidate region, verifies oil vs look-alike (Model 2 YOLO11n), fetches weather and AIS data, runs vessel attribution (Model 3), and returns a unified JSON response.

### Request Format
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file` (UploadFile, required): SAR image tile file (`PNG`, `JPG`, or `TIFF`).
  - `lat` (float, optional, default: `19.05`): Scene center latitude.
  - `lon` (float, optional, default: `72.85`): Scene center longitude.
  - `spill_id` (string, optional): Custom tracking identifier.
  - `search_radius_km` (float, optional, default: `50.0`): Candidate AIS vessel search radius in km.

### Response Schema (`FullAnalysisResponse`)
```json
{
  "analysis_id": "SPILL_A1B2C3D4",
  "timestamp_utc": "2026-09-12T12:00:00Z",
  "location": {
    "lat": 19.05,
    "lon": 72.85
  },
  "detection": {
    "spill_detected": true,
    "confidence": 0.92,
    "centroid": { "lat": 19.052, "lon": 72.854 },
    "area_km2": 4.15,
    "bounding_box": {
      "min_lat": 19.048,
      "min_lon": 72.849,
      "max_lat": 19.056,
      "max_lon": 72.859
    },
    "mask_polygon": {
      "type": "Polygon",
      "coordinates": [[[72.849, 19.048], [72.859, 19.048], [72.859, 19.056], [72.849, 19.056], [72.849, 19.048]]]
    },
    "model": "AttentionUNet"
  },
  "classification": {
    "oil_detected": true,
    "max_confidence": 0.89,
    "oil_probability": 0.89,
    "lookalike_probability": 0.11,
    "classification": "oil",
    "detections": [
      {
        "box": [42.0, 35.0, 210.0, 185.0],
        "confidence": 0.89,
        "class_id": 0,
        "label": "oil"
      }
    ],
    "imgsz": 640,
    "conf_threshold": 0.25,
    "model": "YOLO11n"
  },
  "weather": {
    "wind_speed_ms": 6.5,
    "wind_direction_deg": 210.0,
    "source": "open-meteo"
  },
  "attribution": {
    "status": "success",
    "ranked_vessels": [
      {
        "vessel_id": "413000111",
        "rank": 1,
        "attribution_score": 0.87,
        "risk_level": "HIGH",
        "explanation": "Vessel trajectory aligned closely with oil slick drift vector during acquisition window."
      }
    ]
  },
  "summary": "Oil spill detected (4.15 km²) with 89.0% oil confidence. Candidate vessel 413000111 ranked highest priority for verification."
}
```

---

## 2. GET `/api/v1/weather/current`

**Purpose**: Fetches current ocean surface wind speed and direction for a given location.

### Request Query Parameters
- `lat` (float, required): Latitude.
- `lon` (float, required): Longitude.

### Example Response
```json
{
  "wind_speed_ms": 5.8,
  "wind_direction_deg": 195.0,
  "latitude": 19.05,
  "longitude": 72.85,
  "source": "open-meteo",
  "is_modelled": true
}
```

---

## 3. GET `/api/v1/vessels/nearby`

**Purpose**: Fetches AIS vessel trajectory records near a specified geographic location.

### Request Query Parameters
- `lat` (float, required): Latitude.
- `lon` (float, required): Longitude.
- `radius_km` (float, default: `50.0`): Radius in kilometers.
- `lookback_hours` (int, default: `12`): Hours to search back.

### Example Response
```json
{
  "latitude": 19.05,
  "longitude": 72.85,
  "radius_km": 50.0,
  "vessel_count": 2,
  "records": [
    {
      "vessel_id": "413000111",
      "timestamp_utc": "2026-09-12T04:00:00Z",
      "latitude": 19.12,
      "longitude": 72.92,
      "speed_knots": 3.5,
      "heading_deg": 225.0
    }
  ]
}
```

---

## 4. GET `/api/v1/satellite/search`

**Purpose**: Searches Copernicus STAC catalog for Sentinel-1 SAR scenes matching space-time query.

### Request Query Parameters
- `min_lat`, `min_lon`, `max_lat`, `max_lon` (floats, required): Bounding box.
- `start_date`, `end_date` (strings, optional): ISO date range.

### Example Response
```json
{
  "count": 1,
  "scenes": [
    {
      "id": "S1A_IW_GRDH_1SDV_20260912T034300_20260912T034325_014295_01A97E_39B8",
      "acquisition_time": "2026-09-12T03:43:00Z",
      "polarization": "VV+VH",
      "orbit_direction": "DESCENDING"
    }
  ]
}
```

---

## 5. GET `/api/v1/health`

**Purpose**: Returns application health status, ML model load status, and external service connectivity metrics.

### Example Response
```json
{
  "status": "healthy",
  "app_name": "BlueTrace AI Backend",
  "version": "1.0.0",
  "models": {
    "model1_attention_unet": {
      "status": "loaded",
      "weights_path": ".../attention_unet_best.pth",
      "device": "cpu"
    },
    "model2_yolo11n_detector": {
      "status": "loaded",
      "weights_path": ".../weights/best.pt",
      "imgsz": 640,
      "conf_threshold": 0.25
    },
    "model3_vessel_attribution": {
      "status": "loaded",
      "mode": "heuristic"
    }
  },
  "external_services": {
    "open_meteo_weather": { "status": "connected", "http_status": 200 },
    "copernicus_stac": { "status": "connected", "http_status": 200 },
    "global_fishing_watch_ais": { "status": "using_cached_sample_data", "api_key_present": false }
  }
}
```
