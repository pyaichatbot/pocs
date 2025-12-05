#!/bin/bash
# Script to run Strix against local codebase (static analysis)

set -e

echo "=========================================="
echo "Running Strix Security Scan (Code Analysis)"
echo "=========================================="
echo ""

# Ensure pipx bin directory is in PATH (if pipx was used to install)
if [ -d "$HOME/.local/bin" ] && [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# Set DOCKER_HOST for macOS Docker Desktop (if not already set)
if [ -z "$DOCKER_HOST" ]; then
    # Check for macOS Docker Desktop socket
    if [ -S "$HOME/.docker/run/docker.sock" ]; then
        export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
    # Check for Linux socket
    elif [ -S "/var/run/docker.sock" ]; then
        export DOCKER_HOST="unix:///var/run/docker.sock"
    fi
fi

# Check if Strix is installed
if ! command -v strix &> /dev/null; then
    echo "ERROR: Strix is not installed or not in PATH."
    echo ""
    echo "Install it with:"
    echo "  1. Install pipx: brew install pipx  (macOS) or pip install --user pipx"
    echo "  2. Run: pipx ensurepath"
    echo "  3. Install Strix: pipx install strix-agent"
    echo ""
    echo "Note: Strix requires Python 3.12+ to install."
    exit 1
fi

# Check for required environment variables
if [ -z "$STRIX_LLM" ]; then
    echo "WARNING: STRIX_LLM not set. Using default: openai/gpt-4"
    export STRIX_LLM="${STRIX_LLM:-openai/gpt-4}"
fi

if [ -z "$LLM_API_KEY" ]; then
    echo "ERROR: LLM_API_KEY environment variable is not set."
    echo "Please set it before running this script:"
    echo "  export LLM_API_KEY='your-api-key'"
    exit 1
fi

# Note: Strix doesn't have a built-in environment variable to limit agent count.
# We add an instruction to request single-agent execution to help avoid rate limits.
# This is a request, not a guarantee - Strix may still use multiple agents.

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "Project root: $PROJECT_ROOT"
echo "Target: ./app"
echo "LLM: $STRIX_LLM"
echo ""

# Run Strix against the codebase
cd "$PROJECT_ROOT"

# Build instruction - request single agent to help avoid rate limits
INSTRUCTION="Focus on security vulnerabilities: IDOR, SQL injection, XSS, prompt injection, insecure AI usage, and data leakage. Generate clear PoC and remediation steps. Use a single agent to avoid rate limits."

strix --target ./app \
    --instruction "$INSTRUCTION" \
    || {
        echo ""
        echo "Strix scan completed with findings."
        echo "Results should be in: strix_runs/"
        exit 0
    }

echo ""
echo "Strix scan completed successfully."
echo "Results are in: strix_runs/"

