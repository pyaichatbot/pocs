#!/bin/bash
# Rebuild script for RAG Service
# This ensures code changes are properly included in the Docker image

set -e

cd "$(dirname "$0")"

# Generate build arguments to force cache invalidation
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
BUILD_VERSION=$(git rev-parse --short HEAD 2>/dev/null || echo "dev-$(date +%s)")

echo "Building RAG Service..."
echo "Build Date: $BUILD_DATE"
echo "Build Version: $BUILD_VERSION"

# Build with no cache to ensure all code changes are included
docker build \
  --no-cache \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg BUILD_VERSION="$BUILD_VERSION" \
  -t rag_service-rag-service \
  .

echo "Build complete!"
echo ""
echo "To restart the container:"
echo "  docker restart rag-service"
echo "Or if using docker-compose:"
echo "  docker-compose restart rag-service"

