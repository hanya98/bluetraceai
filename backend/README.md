# BlueTrace — AI Oil Spill Detection & Vessel Attribution Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C.svg?style=flat&logo=pytorch)](https://pytorch.org)
[![Ultralytics](https://img.shields.io/badge/YOLO11n-Ultralytics-00FFFF.svg?style=flat)](https://docs.ultralytics.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Smart India Hackathon 2026 — Problem Statement PS-26143**  
> **Topic**: AI-Based Oil Spill Detection and Suspect Vessel Attribution using Multi-Modal Remote Sensing & AIS Data.

---

## 🌊 Overview

**BlueTrace** is an end-to-end AI-powered backend designed for real-time monitoring of ocean oil spills and automated attribution of potential polluter vessels. Operating on Synthetic Aperture Radar (SAR) imagery acquired by Sentinel-1 satellites, the platform detects oil slicks regardless of cloud cover or daylight conditions.

The system orchestrates a 3-stage artificial intelligence pipeline: an Attention U-Net deep learning model segments marine oil slicks; an Ultralytics YOLO11n object detector verifies spills against natural look-alikes; and a spatiotemporal attribution engine integrates ocean drift physics, wind vectors from Open-Meteo, and Global Fishing Watch AIS vessel trajectories to rank candidate vessels responsible for discharge.

Built with FastAPI, PyTorch, and geospatial libraries (Rasterio, GeoPandas, Shapely), BlueTrace delivers RFC 7946 GeoJSON payloads designed for seamless visual integration with MapLibre frontends.

---

## ✨ Features

- **Model 1 — Attention U-Net Segmentation**: High-precision segmentation of oil slicks from single-band SAR tiles (`untitiled0.ipynb`).
- **Model 2 — Ultralytics YOLO11n Verification**: Object detection model running at `imgsz=640` and `conf=0.25` on candidate region crops (`oil-spill-lookalike-classifier (1).ipynb`).
- **Model 3 — AIS Vessel Attribution**: Spatiotemporal drift modeling and ranking engine (`MODEL3_SIH_2026-main`).
- **Geospatial Vectorization**: Rasterio Affine transforms convert binary mask pixels directly into WGS84 GeoJSON polygons with precise surface area calculations (km²).
- **External Services Integration**: Asynchronous clients for Copernicus STAC catalog, Open-Meteo surface wind parameters, and Global Fishing Watch AIS API.
- **Production Performance**: One-time model weight loading via FastAPI lifespan context manager with asynchronous thread executors.

---

## 🛠️ Tech Stack

- **Framework**: FastAPI, Pydantic v2
- **Machine Learning**: PyTorch, Ultralytics YOLO11n, XGBoost, SHAP
- **Geospatial Engine**: Rasterio, GeoPandas, Shapely, PyPROJ
- **Database**: PostgreSQL with PostGIS extensions (SQLAlchemy 2.0 async)
- **HTTP Client**: HTTPX (async HTTP connections)
- **Containerization**: Docker, Docker Compose

---

## 📁 Repository Structure

```
.
├── app/
│   ├── main.py                 # FastAPI Application instance & CORS middleware
│   ├── config.py               # Pydantic v2 settings & environment manager
│   ├── lifespan.py             # Model weight preloading lifecycle manager
│   ├── dependencies.py         # FastAPI dependency injection
│   ├── models/                 # Model wrappers (AttentionUNet, YOLO11n, Model3)
│   ├── services/               # Core business logic (segmentation, classification, attribution)
│   ├── external/               # Async clients (Sentinel STAC, GFW AIS, Open-Meteo)
│   ├── schemas/                # OpenAPI request/response contracts
│   ├── database/               # PostGIS ORM models
│   ├── utils/                  # Geospatial affine & polygon vectorization utilities
│   └── routes/                 # Endpoint routers (public, internal, utility, health)
├── weights/                    # Checkpoint directory (.gitkeep tracked; .pth/.pt ignored)
│   ├── attention_unet_best.pth # (Place Model 1 weights here)
│   └── best.pt                 # (Place Model 2 YOLO11n weights here)
├── docs/                       # Technical documentation
│   ├── API_REFERENCE.md        # Public REST API documentation
│   ├── ARCHITECTURE.md         # Technical architecture & dependency specification
│   └── SYSTEM_FLOW.md          # End-to-end pipeline flow & ASCII diagram
├── .env.example                # Template for environment variables
├── .gitignore                  # Git ignore rules for weights, datasets & caches
├── Dockerfile                  # Production container definition
├── docker-compose.yml          # Container orchestration (API + PostGIS)
├── requirements.txt            # Python dependency definitions
├── LICENSE                     # MIT License
└── README.md                   # Project README
```

---

## 🚀 Quick Start & Installation

### Prerequisites

- Python 3.10+
- GDAL / PROJ (installed automatically with `rasterio` / `geopandas` wheels on Windows/Linux)
- Git

### 1. Clone & Setup Environment

```bash
git clone https://github.com/your-username/bluetrace-backend.git
cd bluetrace-backend

# Create virtual environment
python -m venv venv
# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### 3. Place Model Weights

Place your trained weights in the `weights/` directory:
- Model 1: `MODEL3_SIH_2026-main/MODEL3_SIH_2026-main/attention_unet_best.pth`
- Model 2: `weights/best.pt`

*(If weights are missing, the backend operates gracefully in stub/fallback mode).*

### 4. Run Locally

```bash
uvicorn app.main:app --reload --port 8000
```

Access the interactive Swagger documentation at `http://localhost:8000/docs`.

---

## 🐳 Docker Deployment

To run the API alongside a PostGIS database container:

```bash
docker-compose up --build -d
```

The API will be available at `http://localhost:8000`.

---

## 📡 API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/analyze` | `POST` | Primary public orchestration endpoint (SAR Image → GeoJSON + Attribution) |
| `/api/v1/weather/current` | `GET` | Current ocean surface wind parameters (Open-Meteo) |
| `/api/v1/vessels/nearby` | `GET` | Nearby candidate AIS vessel tracks |
| `/api/v1/satellite/search` | `GET` | Copernicus STAC catalog Sentinel-1 SAR scene search |
| `/api/v1/health` | `GET` | Detailed health & ML model status |

Detailed request/response contracts are provided in [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md).

---

## ⚙️ Environment Variables

| Variable | Default Value | Description |
|---|---|---|
| `APP_NAME` | `BlueTrace AI Backend` | Application title |
| `APP_VERSION` | `1.0.0` | Application version |
| `DEBUG` | `false` | Enable debug logging |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `MODEL1_WEIGHTS_PATH` | `.../attention_unet_best.pth` | Absolute/relative path to Model 1 weights |
| `MODEL2_WEIGHTS_PATH` | `weights/best.pt` | Path to Model 2 YOLO11n weights |
| `MODEL2_IMGSZ` | `640` | YOLO inference image size |
| `MODEL2_CONF` | `0.25` | YOLO confidence threshold |
| `MODEL3_MODE` | `heuristic` | Model 3 scoring mode (`heuristic` or `ml`) |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostGIS connection string |
| `COPERNICUS_CLIENT_ID` | `None` | Client ID for Copernicus Data Space |
| `GFW_API_KEY` | `None` | API Key for Global Fishing Watch AIS data |
| `INFERENCE_DEVICE` | `cpu` | PyTorch inference device (`cpu` or `cuda`) |

---

## 🔮 Future Improvements

1. **GPU Acceleration**: Deploy Model 1 & Model 2 on CUDA-enabled GPU worker pools for sub-second scene inference.
2. **Sentinel-2 Optical Fusion**: Integrate Sentinel-2 optical bands when cloud coverage allows to refine oil slick thickness classification.
3. **Live AIS Streaming**: Connect to real-time WebSockets AIS feeds for active maritime surveillance.

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
