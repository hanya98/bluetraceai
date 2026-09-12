"""
main.py
=======
FastAPI Application Entry Point.
Configures CORS, lifespan, and mounts all route endpoints under `/api/v1`.
"""
from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.lifespan import lifespan
from app.routes import analyze, attribute, classify, detect, health, satellite, vessels, weather

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "BlueTrace AI Backend — Production FastAPI orchestration platform for "
        "SIH 2026 PS-26143: AI-Based Oil Spill Detection and Vessel Attribution."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
API_PREFIX = "/api/v1"

app.include_router(analyze.router, prefix=API_PREFIX)
app.include_router(detect.router, prefix=API_PREFIX)
app.include_router(classify.router, prefix=API_PREFIX)
app.include_router(attribute.router, prefix=API_PREFIX)
app.include_router(satellite.router, prefix=API_PREFIX)
app.include_router(vessels.router, prefix=API_PREFIX)
app.include_router(weather.router, prefix=API_PREFIX)
app.include_router(health.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    """Root endpoint returning API meta information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{API_PREFIX}/health",
        "primary_endpoint": f"{API_PREFIX}/analyze",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
