# Multi-stage Dockerfile for RAG Service
# Build stage: Install dependencies and build packages
# Build argument to force cache invalidation when code changes
ARG BUILD_DATE
ARG BUILD_VERSION
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies (including LEANN system dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    libomp-dev \
    libboost-all-dev \
    protobuf-compiler \
    libzmq3-dev \
    pkg-config \
    libabsl-dev \
    libaio-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage: Minimal production image
FROM python:3.11-slim as runtime

# Add build metadata for cache invalidation
ARG BUILD_DATE
ARG BUILD_VERSION
LABEL build_date="${BUILD_DATE}" \
      build_version="${BUILD_VERSION}"

WORKDIR /app

# Install only runtime dependencies (including LEANN runtime libs)
# LEANN requires these system libraries at runtime for its native extensions
# Note: libaio-dev includes runtime libs, so we use dev packages for consistency
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libomp-dev \
    libboost-system-dev \
    libboost-filesystem-dev \
    libprotobuf-dev \
    libzmq5 \
    libabsl-dev \
    libaio-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
# Copy all files except those in .dockerignore to maintain rag_service package structure
# Copy directories first to ensure any file change invalidates cache
# Note: Docker cache is based on file checksums, so any modification will invalidate the layer
COPY services/ ./rag_service/services/
COPY utils/ ./rag_service/utils/
COPY repositories/ ./rag_service/repositories/
COPY static/ ./rag_service/static/
COPY __init__.py api.py config.py llm_client.py ./rag_service/
COPY main.py ./

# Create non-root user for security
# Create data directories and set permissions
RUN useradd -m -u 1000 raguser && \
    mkdir -p /app/data/indexes /app/data/chromadb && \
    chown -R raguser:raguser /app

USER raguser

# Expose port
EXPOSE 8000

# Health check (using curl instead of requests for smaller image)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

