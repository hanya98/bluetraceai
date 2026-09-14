# Multi-stage Dockerfile for BlueTrace FastAPI Backend
FROM python:3.10-slim as builder

WORKDIR /app

# Install system dependencies for geospatial tools (GDAL/GEOS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim

WORKDIR /app

# Copy installed dependencies and system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal30 \
    libgeos-c1v5 \
    libproj22 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local
COPY . /app

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
