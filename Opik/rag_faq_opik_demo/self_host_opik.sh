#!/usr/bin/env bash
set -euo pipefail

# Self-host Opik locally using the official opik.sh script
# Usage:
#   bash self_host_opik.sh
#
# Requirements:
#   - Docker Desktop (or Docker Engine) running
#   - Git installed

REPO_URL="https://github.com/comet-ml/opik.git"
REPO_DIR="opik"

echo "[opik] Checking dependencies..."
if ! command -v git >/dev/null 2>&1; then
  echo "[opik] ERROR: git is not installed. Please install git and try again." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[opik] ERROR: Docker is not installed. Please install Docker Desktop and try again." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "[opik] ERROR: Docker daemon is not running. Please start Docker Desktop and try again." >&2
  exit 1
fi

echo "[opik] Preparing repository in $(pwd)/${REPO_DIR}"
if [ ! -d "${REPO_DIR}/.git" ]; then
  echo "[opik] Cloning ${REPO_URL}..."
  git clone "${REPO_URL}" "${REPO_DIR}"
else
  echo "[opik] Repository exists. Pulling latest changes..."
  git -C "${REPO_DIR}" fetch --all --prune
  git -C "${REPO_DIR}" reset --hard origin/main
fi

echo "[opik] Starting Opik platform via opik.sh..."
cd "${REPO_DIR}"
chmod +x ./opik.sh || true
./opik.sh

echo "[opik] If this is the first run, containers will take a bit to initialize."
echo "[opik] Once up, access the UI in your browser (see opik.sh output for URL)."

