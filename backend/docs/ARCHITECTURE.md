# BlueTrace Backend — Technical Architecture Specification

> **SIH 2026 Problem Statement PS-26143: AI-Based Oil Spill Detection and Vessel Attribution**

---

## 1. Architectural Overview

BlueTrace Backend is a production-ready, async-first FastAPI service engineered to orchestrate three distinct AI/ML models alongside external geospatial and environmental APIs.

```
app/
├── main.py                 # FastAPI Application instance & CORS middleware
├── config.py               # Pydantic v2 settings & environment variable manager
├── lifespan.py             # Application startup/shutdown context manager
├── dependencies.py         # FastAPI Dependency Injection singletons
│
├── models/                 # Model inference wrappers & architecture definitions
│   ├── model1_arch.py      # AttentionUNet PyTorch model definition
│   ├── model1_loader.py    # Model 1 inference wrapper with exact notebook preprocessing
│   ├── model2_loader.py    # Model 2 Ultralytics YOLO11n object detector wrapper
│   └── model3_loader.py    # Model 3 Model3Pipeline wrapper & sys.path handler
│
├── services/               # Core business logic layer
│   ├── spill_detection.py  # Model 1 segmentation + region crop + GeoJSON vectorization
│   ├── classification.py   # Model 2 YOLO11n object detection service
│   └── attribution.py      # Model 3 vessel ranking pipeline service
│
├── external/               # Async HTTP API clients (httpx)
│   ├── sentinel_client.py  # Copernicus STAC Sentinel-1 GRD catalog search client
│   ├── ais_client.py       # Global Fishing Watch AIS API client + cached dataset fallback
│   └── weather_client.py   # Open-Meteo ocean wind API client
│
├── utils/                  # Utility functions
│   └── geo_utils.py        # Rasterio Affine transforms, Shapely vectorization & area (km²)
│
├── schemas/                # Pydantic v2 data validation contracts
│   ├── common.py           # Coordinates, BoundingBox, GeoJSONPolygon
│   ├── detection.py        # Model 1 detection request/response contracts
│   ├── classification.py   # Model 2 YOLO11n detection contracts
│   ├── attribution.py      # Model 3 attribution contracts
│   └── pipeline.py         # Unified /api/v1/analyze orchestrator response
│
├── database/               # PostGIS database ORM models
│   └── models.py           # SQLAlchemy ORM models (SpillRecordDB, AttributionDB)
│
└── routes/                 # FastAPI endpoint routers
    ├── analyze.py          # Primary public orchestration endpoint (POST /api/v1/analyze)
    ├── detect.py           # [Internal/Debug] Model 1 segmentation test
    ├── classify.py         # [Internal/Debug] Model 2 YOLO11n test
    ├── attribute.py        # [Internal/Debug] Model 3 attribution test
    ├── satellite.py        # [Utility] Copernicus STAC search
    ├── vessels.py          # [Utility] AIS vessel tracks
    ├── weather.py          # [Utility] Open-Meteo wind query
    └── health.py           # [System] Health check & model/external service status
```

---

## 2. Lifespan & Model Lifecycle

All machine learning models are instantiated **once** during application startup inside `app/lifespan.py` and stored in `app.state`. This guarantees that model weights (`attention_unet_best.pth`, `best.pt`) are never re-read from disk during request processing.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Model 1: Attention U-Net
    app.state.model1 = Model1Inference(weights_path=settings.MODEL1_WEIGHTS_PATH)
    # Model 2: Ultralytics YOLO11n
    app.state.model2 = Model2Inference(weights_path=settings.MODEL2_WEIGHTS_PATH)
    # Model 3: Vessel Attribution Pipeline
    app.state.model3 = Model3Inference()
    yield
```

---

## 3. Dependency Injection Pattern

Routes access pre-loaded model instances via FastAPI dependency injection defined in `app/dependencies.py`:

```python
def get_model1(request: Request) -> Model1Inference:
    return request.app.state.model1

def get_model2(request: Request) -> Model2Inference:
    return request.app.state.model2

def get_model3(request: Request) -> Model3Inference:
    return request.app.state.model3
```

---

## 4. Async & Thread Pool Safety

PyTorch CPU inference and heavy pandas/shapely operations run inside `asyncio.get_running_loop().run_in_executor()` thread pools. This keeps the FastAPI event loop responsive while performing CPU-bound inference.

---

## 5. Model 3 Dynamic Integration

Model 3 (`MODEL3_SIH_2026-main`) is an existing Python package. `app/models/model3_loader.py` dynamically injects the package path into `sys.path` at application boot and imports `Model3Pipeline` without modifying its internal source code.
