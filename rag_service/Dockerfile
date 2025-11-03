# Multi-stage Dockerfile for RAG Service
# Build stage: Install dependencies and build packages
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage: Minimal production image
FROM python:3.11-slim as runtime

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
# Copy all files except those in .dockerignore to maintain rag_service package structure
COPY __init__.py api.py config.py llm_client.py ./rag_service/
COPY repositories/ ./rag_service/repositories/
COPY services/ ./rag_service/services/
COPY utils/ ./rag_service/utils/
COPY static/ ./rag_service/static/
COPY main.py ./

# Create non-root user for security
RUN useradd -m -u 1000 raguser && \
    chown -R raguser:raguser /app

USER raguser

# Expose port
EXPOSE 8000

# Health check (using curl instead of requests for smaller image)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

