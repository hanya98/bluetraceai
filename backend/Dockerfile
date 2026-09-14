# ===========================
# BlueTrace AI Backend Dockerfile
# Render (CPU) Optimized
# ===========================

FROM python:3.10-slim AS builder

WORKDIR /app

# Build dependencies + OpenCV runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python dependencies (CPU-only torch comes from requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Verify PyTorch CPU installation during build
RUN python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"

# ===========================
# Runtime Image
# ===========================

FROM python:3.10-slim

WORKDIR /app

# Runtime libraries required by GDAL + OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local
COPY . /app

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Render injects PORT=10000 automatically
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]